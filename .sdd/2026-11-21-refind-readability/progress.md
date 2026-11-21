# SDD ledger — plan: /home/m/Documents/deepseek-harness/default-workspace/docs/superpowers/plans/2026-11-21-refind-readability.md

Setup: Ruling: sdd-workspaceはgitリポジトリ外のため実行できなかった。利用者の「git操作は勝手に行わない」という指示を優先し、git initせず `refind-menu-fit/.sdd/2026-11-21-refind-readability/` にledgerを手動作成した — 誤って別計画の記録を汚染するリスクは、計画名を先頭に固定して回避する。
Setup: Ruling: task-start/task-done/review-packageもgit前提のため使わず、計画の各タスクを直接読み、テスト結果をこのledgerへ手動記録する — 自動記録の形式は使えないが、各RED/GREENの出力を残す。
Pre-flight: Task 1の `make_kernel_icon` / `create_kernel_icons` → Task 3が利用。インターフェース一致。
Pre-flight: Task 2の `apply_background_effects` / `VARIANTS` / `PANEL_BOX` → Task 3が利用。インターフェース一致。
Pre-flight: Task 3のCLI `--variant` → Task 4が利用。インターフェース一致。
Pre-flight: 作業ツリーはgitではなく、worktreeを作らない。利用者のNative実行とgit禁止を優先。
Task 1: complete (tests: `python3 -m unittest refind-menu-fit/tests/test_readability.py -v` → 2/2 PASS。RED: FileNotFoundError 2件を確認後に実装。ファイル名マッピングの失敗1件を修正してGREEN)
Task 2: complete (tests: 同上 → 5/5 PASS。RED: `apply_background_effects` / `PANEL_BOX` 不在3件を確認後に実装)
Task 3: complete (tests: 同上 → 9/9 PASS。RED: `variant` / `label_font_for_width` / improved theme.conf 不在4件を確認後に実装。既存 `renders/background.png` とのピクセル一致も確認)
Task 4: complete (A1/A2/A3の2560×1440・1280×720、比較シート2種、`reviews/readable-render-ranking.json` を生成。画像比較は1回のAPI呼び出しでA1推奨)
A1 install: complete (ESP に `themes/MomoneChinoi-readable/` 一式とカーネル同名アイコン3つを配置し、`refind.conf` の include を差し替えた。`showtools` はそのまま)
Install ruling: A1 採用 — 利用者が「A1結構いい、それで実装しちゃっていいよ」と明示許可。再起動は行わず、利用者が起動画面を見てタイミングを決める。
Install ruling: バックアップは `/boot/EFI/refind/backups/20261121-182453` (`refind.conf` と `/boot/vmlinuz-linux.png` / `vmlinuz-linux-lts.png` / `vmlinuz-linux-pf.png`)。ロールバックは backups/ から復元で足りる。
Post-install fix (regression): `/boot` 直下へラベル入りカーネルアイコンを配置した結果、`test_original_variant_matches_existing_render_pixel_for_pixel` が失敗した（差分 bbox=(992,758,1417,784)）。原因: シミュレータが `/boot/vmlinuz-linux.png` を入力にしていた → 対応: インストール前の原版を `refind-menu-fit/base-icons/` に保存し、simulate_refind.py がそれを参照するように修正。suite 10/10 GREEN。インストール前の原版の sha256 先頭: vmlinuz-linux(.ORIG互換 d010977eab52) のみ必要。
Final review: self-review (利用者のレート制限回避指示のためsubagent不使用)。計画との整合、コード、テスト、適用素材を確認。
Final: fixed Important「カーネル同名アイコンはloaderと同じESPルートに必要」— `test_improved_install_staging_is_complete` RED→GREEN、`improved/esp-root/` へ3ファイルを配置、suite 10/10。
Final: fixed Important「icons_dirにツール/Windowsアイコンがなく既定iconsへfallbackする」— 同テストRED→GREEN、現行hiresの全アイコンを `improved/icons/` へ配置、suite 10/10。
Final: fixed Important「theme.confが参照する背景ファイルが未生成」— 同テストRED→GREEN、A1の `improved/background.png` を生成、suite 10/10。
Final: minor (deferred): 極端に長いエントリ名は18pxでもパネル幅を超える可能性がある。実機のrEFIndはフォント縮小をしないため、再現側の近似として記録する。
Final: minor (deferred): OSバッジはアイコン右下のラベル帯の枠と重なるが、短いカーネル名自体は中央に保持されている。
