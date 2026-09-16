---
inclusion: always
---

# 技術スタック

- **言語 / ランタイム**: Python 3.x（3.12.6 で import 確認済み）。単一パッケージ `_kyodaishiki/`、ビルドツールなし、`python _main.py` で起動。
- **主要ライブラリ**: `docopt`（コマンド構文）、`winshell`、`chardet`、`colorama`、`python-dateutil`。拡張（`shells/`）は `crayons` / `beautifulsoup4` / `requests` / `selenium` / `pykakasi` / `googletrans`。`requirements.txt` は未整備。
- **永続化**: 外部 DB なし。ディレクトリ単位のプレーンテキスト（`data.txt` / `card.txt` / `tag.txt` / `tot.txt`）。データは既定で `%USERPROFILE%\kyodaishiki2\default_loader_home\` 配下（リポジトリ外）。
- **通信**: 標準ライブラリ `socketserver` による平文 TCP。Home サーバー `127.0.0.1:10000`、DB サーバーはランダムポート、DNS `127.0.0.1:31103`。認証なし。
- **プラットフォーム**: Windows 前提（`%USERPROFILE%` 展開、`winshell`、`sjis` デコード）。
- **コーディング規約**: インデントはタブ。テストなし。コマンド構文は docopt の `Usage:` 文字列が仕様。

コマンドや設定の詳細をここに重複して書かず、更新時は必ず [docs/architecture.md](../../docs/architecture.md) / [docs/cli.md](../../docs/cli.md) 側を更新すること。
