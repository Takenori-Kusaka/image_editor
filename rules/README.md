# ルールファイル（証明写真テンプレート）

日本の主要な証明写真規格を JSON 形式でまとめたテンプレート集です。  
各ファイルには **印刷サイズ・デジタル規格・顔位置ガイド・NG 例** などが含まれており、`image-editor` の設定ファイルとしてそのまま利用できるパラメータも記載しています。

---

## 収録テンプレート

| ファイル | 用途 | サイズ (mm) | ピクセル (300dpi) |
|---|---|---|---|
| `mynumber_card.json` | マイナンバーカード | 35 × 45 | 413 × 531 |
| `passport_photo.json` | パスポート (ICAO 準拠) | 35 × 45 | 413 × 531 |
| `resume_photo.json` | 履歴書 | 30 × 40 | 354 × 472 |
| `drivers_license.json` | 運転免許証 | 24 × 30 | 283 × 354 |

---

## JSON 構造

各ルールファイルは共通のセクションで構成されています。

```
{
  "_meta":                  ... メタ情報（出典・最終確認日・有効期間）
  "print_spec":             ... 印刷時の物理サイズ (mm, dpi)
  "digital_spec":           ... デジタル提出規格 (px, ファイル形式, 容量制限)
  "image_editor_settings":  ... image-editor CLI/GUI 用の推奨設定値
  "face_positioning":       ... 顔の位置・サイズガイドライン
  "composition_rules":      ... 撮影構図ルール（正面・背景・眼鏡等）
  "ng_examples":            ... 不受理となる写真の例
}
```

### `_meta`
- `name` / `name_en` — 日本語名・英語名
- `source` / `source_url` — 公式出典
- `last_verified` — 規格を最後に確認した日付
- `validity_period` — 写真の有効期間（例: 撮影から6ヶ月以内）

### `image_editor_settings`
`image-editor` の設定ファイル (`~/.config/image_editor/settings.json`) に直接マージ可能なパラメータです。

| キー | 説明 |
|---|---|
| `resize_width` / `resize_height` | リサイズ先ピクセル |
| `jpeg_quality` | JPEG 品質 (1-100) |
| `face_style` | 顔検出スタイル (`real` / `anime` / `profile`) |
| `face_padding` | 顔周辺のパディング比率 |
| `bg_method` | 背景除去手法 (`grabcut` / `flood`) |
| `bg_color` | 背景色 `[R, G, B]` |
| `output_format` | 出力フォーマット |

---

## 使い方

### 1. 設定ファイルとして利用

ルールファイル内の `image_editor_settings` を抽出して設定ファイルとして保存し、CLI の `--settings-file` オプションで指定します。

```bash
# 例: パスポート写真用の設定で処理
image-editor resize input.jpg output.jpg --settings-file rules/passport_photo.json
```

> **注意**: 現在の `Settings` クラスは `image_editor_settings` キーを直接読み込む機能には対応していません。将来のバージョンで `--rule-file` オプションの追加を予定しています。手動で `image_editor_settings` の値を設定ファイルにコピーして使用してください。

### 2. プリセットサイズとして利用

`image_editor/operations/crop.py` の `PRESET_SIZES` に以下のプリセットが既に含まれています:

```python
PRESET_SIZES = {
    "id_photo": (600, 800),       # 3×4cm @ 200dpi
    "passport": (413, 531),        # 35×45mm @ 300dpi
    ...
}
```

ルールファイルの規格に合わせて追加・カスタマイズが可能です:

```python
# 例: ルールファイルの規格を追加
"mynumber": (413, 531),       # 35×45mm @ 300dpi
"resume": (354, 472),          # 30×40mm @ 300dpi
"drivers_license": (283, 354), # 24×30mm @ 300dpi
```

### 3. バリデーション用リファレンス

`face_positioning` や `composition_rules` は、出力画像が規格に適合しているか確認するためのリファレンスとして利用できます。

---

## 出典・免責事項

- 各規格は公式サイト（外務省、デジタル庁、警察庁等）の情報に基づいていますが、規格は変更される場合があります。
- 申請前に必ず最新の公式情報をご確認ください。
- `last_verified` フィールドで最終確認日を記録しています。

---

## 新しいルールファイルの追加

同じ JSON 構造に従って新しいルールファイルを作成できます:

1. 上記テンプレートのいずれかをコピー
2. `_meta` セクションを更新（名前・出典・確認日）
3. `print_spec` / `digital_spec` を対象規格に合わせて修正
4. `image_editor_settings` を適切な処理パラメータに設定
5. `face_positioning` / `composition_rules` / `ng_examples` を記入

### 追加候補の証明写真規格

- ビザ申請用写真（国別に異なる）
- 学生証・社員証用写真
- 宅地建物取引士証等の資格証用写真
- TOEIC・英検等の試験用写真
