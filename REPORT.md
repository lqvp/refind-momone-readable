# rEFInd 背景画像の調査と再現レンダー

## 結論

rEFInd 0.14.2 のグラフィックスメニューは、OS アイコン行を画面中央に固定配置する。メニューを右側の空き領域へ移す設定項目はない。したがって、今回はメニューの固定位置に合う桃寝ちのいの画像を集め、実際のテーマ素材と座標で再現レンダーを作って比較した。

A1 を `MomoneChinoi-readable` として `/boot` の ESP に適用した。`refind.conf` の `include` は `themes/MomoneChinoi-readable/theme.conf` を参照している。`showtools` は現行のまま。再起動は行っていないため、実機の起動画面での見え方はまだ未検証である。ロールバック用のバックアップは `/boot/EFI/refind/backups/20261121-182453` にある。

新しい候補の推奨は **A: 3rd mini album『だめいぬ♡いんだ♡だっこ』XFD のサムネイル**である。最終レンダー比較では、顔やタイトルロゴとメニューが干渉せず、現行背景より高い評価になった。追加の可読性改善では、カーネル別アイコンと弱いフロストパネルを採用した **A1** が最も高い評価になった。

## 現行設定から確定したメニュー

- OS 側 4 件: `vmlinuz-linux`、`vmlinuz-linux-lts`、`vmlinuz-linux-pf`、Windows Boot Manager
- ツール側 4 件: shutdown、reboot、firmware、exit
- `refind.conf` 内の手動 `menuentry` はすべて `disabled` であり、OS エントリは自動検出される
- `default_selection "linux-pf"` のため、再現では 3 番目の OS アイコンを選択状態にした
- テーマは `MomoneChinoi-hires`、背景は 2560×1440、`banner_scale fillscreen`

## 描画座標

現行テーマは `big_icon_size 128` と `small_icon_size 64` を明示している。`config.c:731-743` は有効なサイズ指定時に `HaveResized=TRUE` とするため、`screen.c:195-201` の HiDPI 自動倍化は適用されない。

| 要素 | 計算 | 2560×1440 での値 |
|---|---|---|
| OS タイル | `128*9/8` | 144×144 |
| ツールタイル | `64*4/3` | 85×85 |
| OS 行 X | 中央寄せ、間隔 8 | 980, 1132, 1284, 1436 |
| OS 行 Y | `1440/2-144/2` | 648 |
| ツール行 X | 中央寄せ、間隔 8 | 1098, 1191, 1284, 1377 |
| ツール行 Y | `648+144+16` | 808 |
| ラベル位置 | `808+85+16` | 909（`hideui label` のため非表示） |
| ヒント 1 行目 | `1440-28*3` | 1356 |
| ヒント 2 行目 | `1440-28*2` | 1384 |

主な根拠は `menu.c:96-97`、`menu.c:1177-1178`、`menu.c:1246-1264`、`menu.c:1808-1809`、`screen.c:452-478`、`text.c:54-70`。選択画像はタイルサイズへ拡縮し、アイコンはタイル内中央に配置する。

## 候補と出典

31 枚を収集し、30 枚の画像審査に成功した。1 枚は取得先の Cloudflare 応答により審査できなかった。審査は画像モデルによる主観評価なので、最終判断は利用者が行う。

### A: だめいぬ XFD（推奨）

- ファイル: `candidates/yt_CPc5SuuOB6k.jpg`
- 出典: [桃寝ちのい — 3rd mini album『だめいぬ♡いんだ♡だっこ』XFD](https://www.youtube.com/watch?v=CPc5SuuOB6k)
- 元画像: 1280×720
- 最終レンダー評価: 9.2
- 良い点: 顔とタイトルロゴを避けられ、メニューの視認性とパステル調の雰囲気が両立する
- 注意点: 2560×1440 では 2 倍拡大になる。動画の 1080p フレームも調べたが、サムネイルと同じ構図のフレームはなかった

### B: 誕生日イラスト

- ファイル: `candidates/danbooru_11901859.jpg`
- 出典: [danbooru 投稿](https://danbooru.donmai.us/posts/11901859)、[原作者の投稿](https://x.com/na_be123/status/2040095992620683621)
- 元画像: 2048×1434
- 最終レンダー評価: 7.8
- 良い点: 華やかで、顔にはメニューが重ならない
- 注意点: アイコンがケーキの装飾に重なり、暗いアイコンの視認性がやや落ちる。日付と `HAPPY BIRTHDAY!` の文字が残る

### C: 海と山の風景

- ファイル: `candidates/danbooru_7012068.png`
- 出典: [danbooru 投稿](https://danbooru.donmai.us/posts/7012068)、[元画像](https://i.pximg.net/img-original/img/2023/11/05/00/45/43/113144911_p4.png)
- 元画像: 2120×1280
- 最終レンダー評価: 7.2
- 良い点: メニューの視認性が高く、顔への干渉もない
- 注意点: 後ろ姿中心で色がくすんでおり、現行テーマの華やかさは弱い

## 再現ファイル

- `simulate_refind.py`: 背景画像へ rEFInd メニューを合成する CLI
- `renders/background_1280.png`: 現行背景の再現
- `renders/yt_CPc5SuuOB6k_1280.png`: 推奨候補の再現
- `renders/danbooru_11901859_1280.png`: 誕生日候補の再現
- `renders/danbooru_7012068_1280.png`: 風景候補の再現
- `final-renders/comparison.jpg`: 現行と 3 候補の比較シート
- `reviews/vision/`: 各候補の画像審査結果
- `reviews/final-render-ranking.json`: 最終レンダー比較の結果
- `base-icons/`: 適用直前に ESP に存在した `/boot/vmlinuz-linux.png`、`/boot/vmlinuz-linux-pf.png`、`themes/MomoneChinoi-hires/icons/os_arch.png` の保存。再現の基準を ESP の変化から分離する。`vmlinuz-linux-lts.png` は適用前には存在しなかった。`base-icons/vmlinuz-linux-lts.png` は適用後のラベル入りアイコンを写したもので、適用前の原版ではない
- `/boot/EFI/refind/themes/MomoneChinoi-readable/`: 適用済みのテーマ
- `/boot/EFI/refind/backups/20261121-182453/`: `refind.conf` とカーネル同名アイコンのバックアップ

適用後に判明した回帰: `/boot/vmlinuz-linux.png` などをラベル入りへ置き換えたため、シミュレータが ESP のファイルを読む設計だと既存 `renders/background.png` をそのまま再現できなくなった。原因は ESP のファイルが唯一の入力だったことにある。`base-icons/` に適用前の原版を保存し、シミュレータはそこを参照するように変更した。これによって `test_original_variant_matches_existing_render_pixel_for_pixel` を含む10件のテストが再び成功している。

再現は実機の起動確認ではない。OS エントリの並び順、ファームウェアが選択する解像度、フォント描画、バッジ表示は実機と差が出る可能性がある。

## 可読性改善

従来の候補Aは `hideui label` のため選択中のカーネル名が出ず、3つのカーネルをアイコンで区別しにくかった。改善版では `linux` / `LTS` / `pf` をアイコンへ埋め込み、選択中のエントリ名をY=909に表示するようにした。

| バリアント | 内容 | 画像比較の評価 |
|---|---|---|
| A1 | 全体ブラー1.4px、パネルブラー10px、白い半透明パネル72/255 | 9 |
| A2 | 全体ブラー1.4px、パネルブラー16px、白い半透明パネル128/255 | 8 |
| A3 | 全体ブラー3.0px、選択名の背後だけ薄い帯を追加 | 7 |
| 従来A | ラベルとパネルなし | 4 |

推奨はA1である。A2は文字のコントラストが高い一方で白いパネルの主張が強く、A3は絵を多く残せる一方で服の柄とアイコンが重なって見える。

- `final-renders/comparison-readable.jpg`: 従来AとA1/A2/A3の比較
- `final-renders/comparison-readable-zoom.jpg`: カーネル名と選択名を拡大した比較
- `reviews/readable-render-ranking.json`: 改善版の画像比較結果
- `improved/background.png`: A1のブラーとパネルを合成した背景
- `improved/theme.conf`: `hideui label` を外した適用候補
- `improved/icons/`: 現行テーマの全アイコンとカーネル別アイコン
- `improved/esp-root/`: ローダーと同じディレクトリに置く3つのカーネル別アイコン

カーネル同名のアイコンは `scan.c:486-491` でローダーと同じディレクトリから読まれるため、`vmlinuz-linux.png` / `vmlinuz-linux-lts.png` / `vmlinuz-linux-pf.png` はESPルート側にも必要である。テストは10件すべて成功し、既存の再現出力が変わっていないこともピクセル単位で確認した。

ブラーとパネルは背景画像へ焼き込む方式である。実機のrEFIndは選択名のフォントを自動で縮小しないため、長いエントリ名の表示は再現と異なる可能性がある。

## 作業上の記録

- 画像審査用のサブエージェントは、プロバイダー側の予算・レート制限で繰り返し失敗した。以後はサブエージェントを増やさず、画像 API を逐次実行に切り替えた
- API 呼び出しは 12 秒間隔にし、最終比較は 1 回にまとめた
- ESP 上の `refind.conf` は適用後、A1 のテーマを参照している。`themes/MomoneChinoi-hires/` は削除せず残してある
- 前段で作成した未使用の `MomoneChinoi-side` は削除せず残っている。現行設定からは参照されていない
- 適用前に `/boot/vmlinuz-linux.png` と `vmlinuz-linux-pf.png` は存在しており、どちらも適用によって差し替えた。両方の原版は `/boot/EFI/refind/backups/20261121-182453/` にある。`/boot/vmlinuz-linux-lts.png` は適用前には存在せず、バックアップは不要だった（適用時に新規配置した）
- サブエージェントを利用者の指示で gemini-oauth へ寄せる話は、このセッションでは実行できなかった。許可ルートが `mistral` のみであり、プロファイル側の設定は後から更新されていてもこのセッションのポリシーは変更されない。新しいセッションでは Web プロファイル側の許可リストから gemini-oauth のルートを選べるはずである
