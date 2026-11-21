# rEFInd Readability Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-subagent-driven-development (recommended) or superpowers-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 候補Aの背景に、カーネル識別用アイコン、選択名表示、ブラー、フロストパネルを加えた3種類の再現画像と適用候補素材を作る。

**Architecture:** 既存の `simulate_refind.py` を後方互換のまま拡張し、背景変換とカスタムアイコンを差し替え可能にする。画像生成と効果は `readability_assets.py` に分け、標準ライブラリ `unittest` で挙動を検証する。

**Tech Stack:** Python 3、Pillow、組み込み `unittest`

**Spec:** `refind-menu-fit/DESIGN-readability.draft.md`

## Global Constraints

- ESPと `/boot` への書き込み、再起動、git操作は行わない
- 既存の `python3 simulate_refind.py BACKGROUND` の出力を変えない
- OS座標はX=980,1132,1284,1436/Y=648、ツールはX=1098,1191,1284,1377/Y=808を維持する
- 選択名はY=909に表示し、再現では `Boot vmlinuz-linux-pf` を使う
- サブエージェントはレート制限のため新規に使わず、画像APIの比較は1回にまとめる

## Review Focus

- 自動検出の長いエントリ名がパネルからはみ出す可能性: 長さ60文字のラベルでも画像外に出ないことをTask 3で検査する
- カーネルの検出順が変わる可能性: 名前を背景ではなくアイコンに埋め込むことをTask 1で検査する
- パネルがキャラの顔に掛かる可能性: パネル右端が画面幅の68%未満であることをTask 2で検査する
- 低解像度画像をぼかしすぎる可能性: A1/A2の全体ブラーは1.4px、A3は3.0pxに固定してTask 2で検査する
- 既存再現の回帰: 変更前の `renders/background.png` とデフォルト出力の一致をTask 3で検査する

---

### Task 1: カーネル別アイコン

**Files:**
- Create: `refind-menu-fit/readability_assets.py`
- Create: `refind-menu-fit/tests/test_readability.py`

**Interfaces:**
- Produces: `make_kernel_icon(base_path: Path, label: str, accent: tuple[int, int, int], output_path: Path) -> None`
- Produces: `create_kernel_icons(output_dir: Path) -> dict[str, Path]`

- [ ] **Step 1: 失敗するテストを書く**

`make_kernel_icon` が128×128を出力し、下部26pxにラベル帯と `accent` のピクセルが10個以上含まれること、`create_kernel_icons` が `vmlinuz-linux.png` / `vmlinuz-linux-lts.png` / `vmlinuz-linux-pf.png` の3ファイルを返すことを検査する。

- [ ] **Step 2: テストが未実装で失敗することを確認する**

Run: `python3 -m unittest refind-menu-fit/tests/test_readability.py -v`
Expected: `ModuleNotFoundError` または対象関数の不在でFAIL

- [ ] **Step 3: アイコン生成を実装する**

既存のArchアイコンをRGBAで読み、下部26pxへ白235/255の帯とaccentの枠・文字を描く。文字は `linux`=20px、`LTS` / `pf`=24pxのDejaVu Sans Mono Boldとする。

- [ ] **Step 4: テストが通ることを確認する**

Run: `python3 -m unittest refind-menu-fit/tests/test_readability.py -v`
Expected: 全テストPASS

### Task 2: 背景ブラーとフロストパネル

**Files:**
- Modify: `refind-menu-fit/readability_assets.py`
- Test: `refind-menu-fit/tests/test_readability.py`

**Interfaces:**
- Consumes: Task 1のモジュール
- Produces: `PANEL_BOX = (840, 600, 1720, 980)`
- Produces: `apply_background_effects(image: Image.Image, variant: str) -> Image.Image`
- Produces: `VARIANTS = {"a1": {"overall_blur": 1.4, "panel_blur": 10, "panel_alpha": 72}, "a2": {"overall_blur": 1.4, "panel_blur": 16, "panel_alpha": 128}, "a3": {"overall_blur": 3.0, "panel_blur": 0, "panel_alpha": 0}}`

- [ ] **Step 1: 失敗するテストを追加する**

鋭い矩形を含む2560×1440の試験画像に対し、A1/A2ではパネル内が変化し、A3ではパネルが合成されないこと、全体ブラー値が指定どおりであること、`PANEL_BOX[2] < 2560*0.68` であることを検査する。

- [ ] **Step 2: 新しいテストが失敗することを確認する**

Run: `python3 -m unittest refind-menu-fit/tests/test_readability.py -v`
Expected: `apply_background_effects` 不在でFAIL

- [ ] **Step 3: 背景効果を実装する**

全体をGaussianBlurし、A1/A2では `PANEL_BOX` をさらにぼかした領域へ白い角丸パネルを合成する。A3はパネルを使わず、選択名の背後だけY=896〜944の薄い帯を敷く。rEFInd標準の選択名には影を付けられないため、文字影はアイコン内ラベルだけに限定する。

- [ ] **Step 4: 全テストが通ることを確認する**

Run: `python3 -m unittest refind-menu-fit/tests/test_readability.py -v`
Expected: 全テストPASS

### Task 3: シミュレータへの統合と適用候補

**Files:**
- Modify: `refind-menu-fit/simulate_refind.py`
- Create: `refind-menu-fit/improved/theme.conf`
- Test: `refind-menu-fit/tests/test_readability.py`

**Interfaces:**
- Consumes: `apply_background_effects(image, variant)`、`create_kernel_icons(output_dir)`
- Produces: `render_menu(background_path: Path, *, variant: str = "original", assets_dir: Path | None = None) -> Image.Image`
- Produces: CLI `python3 simulate_refind.py --variant a1 BACKGROUND`

- [ ] **Step 1: 失敗するテストを追加する**

`variant="original"` の出力が既存 `renders/background.png` と一致すること、A1で選択名領域が変化すること、60文字のラベルでも画像内に収まること、改善版 `theme.conf` に `hideui label` がないことを検査する。

- [ ] **Step 2: 新しいテストが失敗することを確認する**

Run: `python3 -m unittest refind-menu-fit/tests/test_readability.py -v`
Expected: `variant` 引数または改善版設定がなくFAIL

- [ ] **Step 3: シミュレータを拡張する**

デフォルト引数は従来どおりとし、`variant` が `a1` / `a2` / `a3` のときだけTask 2の背景効果、Task 1のOSアイコン、Y=909の選択名を有効にする。選択名は中央寄せで、画像幅を超える場合はフォントを28pxから最小18pxまで縮小する。

- [ ] **Step 4: 適用候補の `theme.conf` を作る**

現行 `MomoneChinoi-hires/theme.conf` を基に、背景とアイコンの参照先を将来のESP上の `themes/MomoneChinoi-readable/...` に変え、`hideui label` を削除する。素材はワークスペースの `improved/` に同じ相対構成で置き、実際のESPへは書き込まない。

- [ ] **Step 5: 全テストが通ることを確認する**

Run: `python3 -m unittest refind-menu-fit/tests/test_readability.py -v`
Expected: 全テストPASS

### Task 4: 3種類のレンダーと最終比較

**Files:**
- Create: `refind-menu-fit/renders/a1_readable.png`, `a1_readable_1280.png`
- Create: `refind-menu-fit/renders/a2_readable.png`, `a2_readable_1280.png`
- Create: `refind-menu-fit/renders/a3_readable.png`, `a3_readable_1280.png`
- Create: `refind-menu-fit/comparison-readable.png`
- Modify: `refind-menu-fit/REPORT.md`

**Interfaces:**
- Consumes: Task 3のCLIと改善版素材

- [ ] **Step 1: 3種類をレンダーする**

Run: `python3 refind-menu-fit/simulate_refind.py --variant a1 refind-menu-fit/candidates/yt_CPc5SuuOB6k.jpg`（A2/A3も同様）
Expected: 各2560×1440と1280×720が生成される

- [ ] **Step 2: 比較シートを作る**

現行、従来の候補A、A1、A2、A3を並べ、カーネル名と選択名の拡大領域も別に切り出す。

- [ ] **Step 3: 画像比較を1回だけ実行する**

3種類の再現画像を1回の画像API呼び出しにまとめ、ラベル判別、選択名の可読性、顔への干渉、パステル調の保持を比較する。結果は `reviews/readable-render-ranking.json` に保存する。

- [ ] **Step 4: 結果を報告書へ追記し、yomiyasuで推敲する**

推奨バリアント、各案のトレードオフ、実機未検証であることを記録する。ESPへの適用は行わず、利用者がバリアントを選んだあとに別途確認する。
