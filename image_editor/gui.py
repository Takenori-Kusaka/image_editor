"""GUI entry point for image_editor using tkinter."""

import os
import threading
from pathlib import Path
from tkinter import (
    Tk, ttk, filedialog, messagebox, StringVar, IntVar, BooleanVar,
    Frame, Label, Button, Entry, Checkbutton, OptionMenu, Scale,
    HORIZONTAL, LEFT, RIGHT, TOP, BOTTOM, X, Y, BOTH, W, E, N, S,
    Canvas, Scrollbar, VERTICAL,
)
from PIL import Image, ImageTk

from image_editor.operations import (
    crop_file,
    resize_file,
    convert_file,
    background_file,
    PRESET_SIZES,
    FORMAT_ALIASES,
)
from image_editor.utils.backup import create_backup
from image_editor.utils.batch import batch_process, find_images


PREVIEW_MAX_SIZE = (400, 400)


class ImageEditorGUI:
    """Main GUI application for image_editor."""

    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Image Editor")
        self.root.resizable(True, True)

        self.input_path = StringVar()
        self.output_path = StringVar()
        self.backup_enabled = BooleanVar(value=False)
        self.backup_dir = StringVar()

        self._preview_image = None  # Keep reference to avoid GC

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Build the main UI layout."""
        # Top bar: file selection
        top_frame = Frame(self.root, padx=8, pady=8)
        top_frame.pack(fill=X)

        Label(top_frame, text="Input:").grid(row=0, column=0, sticky=W)
        Entry(top_frame, textvariable=self.input_path, width=40).grid(row=0, column=1, padx=4)
        Button(top_frame, text="Browse", command=self._browse_input).grid(row=0, column=2)

        Label(top_frame, text="Output:").grid(row=1, column=0, sticky=W, pady=4)
        Entry(top_frame, textvariable=self.output_path, width=40).grid(row=1, column=1, padx=4)
        Button(top_frame, text="Browse", command=self._browse_output).grid(row=1, column=2)

        Label(top_frame, text="Backup:").grid(row=2, column=0, sticky=W)
        Checkbutton(top_frame, variable=self.backup_enabled).grid(row=2, column=1, sticky=W, padx=4)
        Label(top_frame, text="Backup dir:").grid(row=3, column=0, sticky=W)
        Entry(top_frame, textvariable=self.backup_dir, width=40).grid(row=3, column=1, padx=4)
        Button(top_frame, text="Browse", command=self._browse_backup_dir).grid(row=3, column=2)

        # Main content: tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=8, pady=4)

        self._build_crop_tab()
        self._build_resize_tab()
        self._build_convert_tab()
        self._build_background_tab()
        self._build_batch_tab()
        self._build_preview_tab()

        # Status bar
        self.status_var = StringVar(value="Ready")
        Label(self.root, textvariable=self.status_var, anchor=W, relief="sunken").pack(
            fill=X, side=BOTTOM, padx=4, pady=2
        )

    # --- Crop Tab ---

    def _build_crop_tab(self):
        frame = Frame(self.notebook, padx=8, pady=8)
        self.notebook.add(frame, text="Crop")

        self._crop_left = IntVar(value=0)
        self._crop_top = IntVar(value=0)
        self._crop_right = IntVar(value=0)
        self._crop_bottom = IntVar(value=0)

        for row, (label, var) in enumerate([
            ("Left:", self._crop_left),
            ("Top:", self._crop_top),
            ("Right:", self._crop_right),
            ("Bottom:", self._crop_bottom),
        ]):
            Label(frame, text=label).grid(row=row, column=0, sticky=W, pady=2)
            Entry(frame, textvariable=var, width=10).grid(row=row, column=1, sticky=W, padx=4)

        Button(frame, text="Crop", command=self._do_crop).grid(row=4, column=0, columnspan=2, pady=8)

    # --- Resize Tab ---

    def _build_resize_tab(self):
        frame = Frame(self.notebook, padx=8, pady=8)
        self.notebook.add(frame, text="Resize")

        self._resize_width = IntVar(value=0)
        self._resize_height = IntVar(value=0)
        self._resize_keep_aspect = BooleanVar(value=False)
        self._resize_preset = StringVar(value="(none)")

        Label(frame, text="Width:").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self._resize_width, width=10).grid(row=0, column=1, sticky=W, padx=4)

        Label(frame, text="Height:").grid(row=1, column=0, sticky=W, pady=2)
        Entry(frame, textvariable=self._resize_height, width=10).grid(row=1, column=1, sticky=W, padx=4)

        Checkbutton(frame, text="Keep aspect ratio", variable=self._resize_keep_aspect).grid(
            row=2, column=0, columnspan=2, sticky=W
        )

        Label(frame, text="Preset:").grid(row=3, column=0, sticky=W, pady=4)
        preset_choices = ["(none)"] + list(PRESET_SIZES.keys())
        OptionMenu(frame, self._resize_preset, *preset_choices).grid(row=3, column=1, sticky=W, padx=4)

        Button(frame, text="Resize", command=self._do_resize).grid(row=4, column=0, columnspan=2, pady=8)

    # --- Convert Tab ---

    def _build_convert_tab(self):
        frame = Frame(self.notebook, padx=8, pady=8)
        self.notebook.add(frame, text="Convert")

        self._convert_format = StringVar(value="png")
        self._convert_quality = IntVar(value=95)

        Label(frame, text="Target format:").grid(row=0, column=0, sticky=W)
        fmt_choices = sorted(set(k.upper() for k in FORMAT_ALIASES) | {"PNG", "JPEG", "WEBP", "GIF", "BMP", "TIFF"})
        OptionMenu(frame, self._convert_format, *fmt_choices).grid(row=0, column=1, sticky=W, padx=4)

        Label(frame, text="Quality (JPEG/WebP):").grid(row=1, column=0, sticky=W, pady=4)
        Scale(
            frame, variable=self._convert_quality, from_=1, to=95, orient=HORIZONTAL, length=200
        ).grid(row=1, column=1, sticky=W, padx=4)

        Button(frame, text="Convert", command=self._do_convert).grid(row=2, column=0, columnspan=2, pady=8)

    # --- Background Tab ---

    def _build_background_tab(self):
        frame = Frame(self.notebook, padx=8, pady=8)
        self.notebook.add(frame, text="Background")

        self._bg_action = StringVar(value="remove")
        self._bg_threshold = IntVar(value=30)
        self._bg_color = StringVar(value="255,255,255")

        Label(frame, text="Action:").grid(row=0, column=0, sticky=W)
        OptionMenu(frame, self._bg_action, "remove", "replace").grid(row=0, column=1, sticky=W, padx=4)

        Label(frame, text="Threshold (0-255):").grid(row=1, column=0, sticky=W, pady=4)
        Scale(
            frame, variable=self._bg_threshold, from_=0, to=255, orient=HORIZONTAL, length=200
        ).grid(row=1, column=1, sticky=W, padx=4)

        Label(frame, text="Replace color (R,G,B):").grid(row=2, column=0, sticky=W)
        Entry(frame, textvariable=self._bg_color, width=15).grid(row=2, column=1, sticky=W, padx=4)

        Button(frame, text="Process Background", command=self._do_background).grid(
            row=3, column=0, columnspan=2, pady=8
        )

    # --- Batch Tab ---

    def _build_batch_tab(self):
        frame = Frame(self.notebook, padx=8, pady=8)
        self.notebook.add(frame, text="Batch")

        self._batch_input_dir = StringVar()
        self._batch_output_dir = StringVar()
        self._batch_operation = StringVar(value="resize")
        self._batch_recursive = BooleanVar(value=False)
        self._batch_overwrite = BooleanVar(value=False)
        self._batch_width = IntVar(value=800)
        self._batch_height = IntVar(value=600)
        self._batch_preset = StringVar(value="(none)")
        self._batch_format = StringVar(value="png")

        Label(frame, text="Input directory:").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self._batch_input_dir, width=35).grid(row=0, column=1, sticky=W, padx=4)
        Button(frame, text="Browse", command=lambda: self._batch_input_dir.set(
            filedialog.askdirectory()
        )).grid(row=0, column=2)

        Label(frame, text="Output directory:").grid(row=1, column=0, sticky=W, pady=4)
        Entry(frame, textvariable=self._batch_output_dir, width=35).grid(row=1, column=1, sticky=W, padx=4)
        Button(frame, text="Browse", command=lambda: self._batch_output_dir.set(
            filedialog.askdirectory()
        )).grid(row=1, column=2)

        Label(frame, text="Operation:").grid(row=2, column=0, sticky=W)
        OptionMenu(frame, self._batch_operation, "resize", "convert", "background").grid(
            row=2, column=1, sticky=W, padx=4
        )

        Checkbutton(frame, text="Recursive", variable=self._batch_recursive).grid(
            row=3, column=0, sticky=W
        )
        Checkbutton(frame, text="Overwrite existing", variable=self._batch_overwrite).grid(
            row=3, column=1, sticky=W
        )

        # Resize options
        Label(frame, text="Width:").grid(row=4, column=0, sticky=W, pady=2)
        Entry(frame, textvariable=self._batch_width, width=8).grid(row=4, column=1, sticky=W, padx=4)
        Label(frame, text="Height:").grid(row=5, column=0, sticky=W)
        Entry(frame, textvariable=self._batch_height, width=8).grid(row=5, column=1, sticky=W, padx=4)
        Label(frame, text="Preset:").grid(row=6, column=0, sticky=W, pady=2)
        OptionMenu(frame, self._batch_preset, *["(none)"] + list(PRESET_SIZES.keys())).grid(
            row=6, column=1, sticky=W, padx=4
        )

        # Format option
        Label(frame, text="Format (for convert):").grid(row=7, column=0, sticky=W, pady=2)
        OptionMenu(frame, self._batch_format, *["png", "jpg", "webp", "bmp", "tiff"]).grid(
            row=7, column=1, sticky=W, padx=4
        )

        Button(frame, text="Run Batch", command=self._do_batch).grid(
            row=8, column=0, columnspan=3, pady=8
        )

        # Log area
        from tkinter import Text
        self._batch_log = Text(frame, height=8, state="disabled", font=("Courier", 9))
        self._batch_log.grid(row=9, column=0, columnspan=3, sticky=BOTH)
        scrollbar = Scrollbar(frame, orient=VERTICAL, command=self._batch_log.yview)
        scrollbar.grid(row=9, column=3, sticky=N + S)
        self._batch_log.configure(yscrollcommand=scrollbar.set)
        frame.rowconfigure(9, weight=1)

    # --- Preview Tab ---

    def _build_preview_tab(self):
        frame = Frame(self.notebook, padx=8, pady=8)
        self.notebook.add(frame, text="Preview")

        Button(frame, text="Load Preview", command=self._load_preview).pack()

        self._preview_canvas = Canvas(frame, bg="#eeeeee", width=420, height=420)
        self._preview_canvas.pack(fill=BOTH, expand=True)
        self._preview_label = Label(frame, text="")
        self._preview_label.pack()

    # ------------------------------------------------------------------
    # File browsing
    # ------------------------------------------------------------------

    def _browse_input(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.gif *.bmp *.tiff *.tif"), ("All files", "*.*")]
        )
        if path:
            self.input_path.set(path)
            # Auto-set output path
            p = Path(path)
            self.output_path.set(str(p.parent / f"{p.stem}_out{p.suffix}"))

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.gif *.bmp *.tiff"), ("All files", "*.*")]
        )
        if path:
            self.output_path.set(path)

    def _browse_backup_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.backup_dir.set(path)

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def _validate_paths(self) -> bool:
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an input file.")
            return False
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify an output file.")
            return False
        if not Path(self.input_path.get()).exists():
            messagebox.showerror("Error", f"Input file not found: {self.input_path.get()}")
            return False
        return True

    def _do_backup(self):
        if self.backup_enabled.get():
            try:
                bp = create_backup(self.input_path.get(), self.backup_dir.get() or None)
                self.status_var.set(f"Backup created: {bp}")
            except Exception as exc:
                messagebox.showwarning("Backup Warning", f"Backup failed: {exc}")

    def _do_crop(self):
        if not self._validate_paths():
            return
        try:
            self._do_backup()
            crop_file(
                self.input_path.get(),
                self.output_path.get(),
                self._crop_left.get(),
                self._crop_top.get(),
                self._crop_right.get(),
                self._crop_bottom.get(),
            )
            self.status_var.set(f"Cropped: {self.output_path.get()}")
            messagebox.showinfo("Done", f"Cropped image saved to:\n{self.output_path.get()}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _do_resize(self):
        if not self._validate_paths():
            return
        try:
            self._do_backup()
            preset = self._resize_preset.get()
            resize_file(
                self.input_path.get(),
                self.output_path.get(),
                self._resize_width.get(),
                self._resize_height.get(),
                keep_aspect=self._resize_keep_aspect.get(),
                preset=preset if preset != "(none)" else None,
            )
            self.status_var.set(f"Resized: {self.output_path.get()}")
            messagebox.showinfo("Done", f"Resized image saved to:\n{self.output_path.get()}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _do_convert(self):
        if not self._validate_paths():
            return
        try:
            self._do_backup()
            convert_file(
                self.input_path.get(),
                self.output_path.get(),
                target_format=self._convert_format.get(),
                quality=self._convert_quality.get(),
            )
            self.status_var.set(f"Converted: {self.output_path.get()}")
            messagebox.showinfo("Done", f"Converted image saved to:\n{self.output_path.get()}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _do_background(self):
        if not self._validate_paths():
            return
        try:
            self._do_backup()
            color_str = self._bg_color.get()
            from image_editor.cli import _parse_color
            color = _parse_color(color_str)
            background_file(
                self.input_path.get(),
                self.output_path.get(),
                action=self._bg_action.get(),
                threshold=self._bg_threshold.get(),
                color=color,
            )
            self.status_var.set(f"Background processed: {self.output_path.get()}")
            messagebox.showinfo("Done", f"Processed image saved to:\n{self.output_path.get()}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _do_batch(self):
        input_dir = self._batch_input_dir.get()
        output_dir = self._batch_output_dir.get()
        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Please specify input and output directories.")
            return

        def run():
            self._batch_log_clear()
            operation = self._batch_operation.get()
            files = find_images(input_dir, recursive=self._batch_recursive.get())
            if not files:
                self._batch_log_write("No image files found.\n")
                return

            self._batch_log_write(f"Found {len(files)} file(s). Processing...\n")

            if operation == "resize":
                from image_editor.operations.resize import resize_file as _resize_file
                preset = self._batch_preset.get()
                results = batch_process(
                    files,
                    _resize_file,
                    output_dir=output_dir,
                    overwrite=self._batch_overwrite.get(),
                    width=self._batch_width.get(),
                    height=self._batch_height.get(),
                    preset=preset if preset != "(none)" else None,
                )
            elif operation == "convert":
                from image_editor.operations.convert import convert_file as _convert_file
                fmt = self._batch_format.get()
                results = batch_process(
                    files,
                    _convert_file,
                    output_dir=output_dir,
                    output_format=fmt,
                    overwrite=self._batch_overwrite.get(),
                    target_format=fmt,
                )
            elif operation == "background":
                from image_editor.operations.background import background_file as _background_file
                results = batch_process(
                    files,
                    _background_file,
                    output_dir=output_dir,
                    output_format="png",
                    overwrite=self._batch_overwrite.get(),
                    action="remove",
                    threshold=30,
                    color=(255, 255, 255),
                )
            else:
                self._batch_log_write(f"Unknown operation: {operation}\n")
                return

            for r in results:
                status = r["status"]
                if status.startswith("error"):
                    self._batch_log_write(f"  ERROR  {Path(r['input']).name}: {status}\n")
                elif status.startswith("skipped"):
                    self._batch_log_write(f"  SKIP   {Path(r['input']).name}\n")
                else:
                    self._batch_log_write(f"  OK     {Path(r['output']).name}\n")

            ok = sum(1 for r in results if r["status"] == "ok")
            errors = sum(1 for r in results if r["status"].startswith("error"))
            self._batch_log_write(f"\nDone: {ok} processed, {errors} errors.\n")

        threading.Thread(target=run, daemon=True).start()

    def _batch_log_clear(self):
        from tkinter import END
        self._batch_log.configure(state="normal")
        self._batch_log.delete("1.0", END)
        self._batch_log.configure(state="disabled")

    def _batch_log_write(self, text: str):
        from tkinter import END
        self._batch_log.configure(state="normal")
        self._batch_log.insert(END, text)
        self._batch_log.see(END)
        self._batch_log.configure(state="disabled")

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _load_preview(self):
        path = self.input_path.get() or self.output_path.get()
        if not path or not Path(path).exists():
            messagebox.showerror("Error", "Please select an input or output file to preview.")
            return
        try:
            with Image.open(path) as img:
                img.thumbnail(PREVIEW_MAX_SIZE, Image.LANCZOS)
                self._preview_image = ImageTk.PhotoImage(img)
                self._preview_canvas.delete("all")
                self._preview_canvas.create_image(
                    self._preview_canvas.winfo_width() // 2,
                    self._preview_canvas.winfo_height() // 2,
                    anchor="center",
                    image=self._preview_image,
                )
                self._preview_label.config(
                    text=f"{Path(path).name} ({img.size[0]}x{img.size[1]})"
                )
        except Exception as exc:
            messagebox.showerror("Error", f"Could not load image: {exc}")


def main():
    """GUI entry point."""
    root = Tk()
    app = ImageEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
