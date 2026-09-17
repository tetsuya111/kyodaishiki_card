# CLAUDE.md

このファイルは、このリポジトリで作業する Claude Code (claude.ai/code) 向けのガイドです。

**このファイルおよび今後の追記・更新はすべて日本語で記述すること。**

## プロジェクト構成

このリポジトリは、京大式カード（梅棹忠夫が提唱した情報カード法）をデジタル化した、対話型シェルベースの個人用カード管理ツール **kyodaishiki** の Python 実装です。単一の Python パッケージからなり、Web フロントエンドや外部 DB は持ちません。

- `_main.py` — エントリポイント。`_kyodaishiki.main()` を呼ぶだけ。
- `_kyodaishiki/` — 本体パッケージ（Python 3、標準ライブラリ + docopt など少数の依存）。
  - `__main__.py` / `__shell__.py` / `__db__.py` / `__index__.py` / `__data__.py` / `__server__.py` / `__dns__.py` / `_util.py` / `_path.py` — コア（CLI 引数解釈、対話シェル階層、カード DB、データモデル、ファイル形式、TCP サーバー/クライアント、簡易 DNS、ユーティリティ）。
  - `shells/` — コアのシェルを継承して機能追加する拡張スクリプト群（書籍管理、レビュー、クローラ、Wikipedia/YouTube/Twitter 連携など）。実験的なコードが多く、コアと比べて品質・整合性は保証されない。
- `docs/` — 要件定義・構成・CLI の詳細ドキュメント（下記）。
- `.kiro/steering/` — 常時参照されるプロダクト前提（product.md / tech.md / structure.md）。

カードデータ（`data.txt` / `card.txt` / `tag.txt` / `tot.txt` など）はリポジトリ外の `%USERPROFILE%\kyodaishiki2\default_loader_home\` 配下に生成される。リポジトリ内にデータファイルをコミットしないこと。

## ドキュメント一覧

詳細は各ドキュメントに一本化しており、このファイルはそこへの索引を兼ねる。新しい詳細情報を追記する際は、このファイルに直接書かず該当ドキュメントを更新すること。

- [README.md](README.md) — 概要、セットアップ、起動方法、最小限の使い方
- [docs/requirements.md](docs/requirements.md) — 要件定義書（用語、機能要件、非機能要件、制約、既知の課題）
- [docs/architecture.md](docs/architecture.md) — プロジェクト構成（起動フロー、モジュール/クラス階層、データモデル、永続化ファイル形式、ネットワーク構成、拡張機構）
- [docs/cli.md](docs/cli.md) — 対話シェルの階層ごとのコマンドリファレンス

## 開発ワークフロー（`.kiro/`）

AWS Kiro の Steering / Specs / Agent Hooks の考え方を `.kiro/` 配下で再現する。

- [.kiro/steering/](.kiro/steering/) — 常時参照される永続的なプロジェクトコンテキスト（product.md / tech.md / structure.md）。詳細は `docs/` にあり、steering からはリンクのみ行う。
- `.kiro/specs/` — 機能ごとの requirements.md → design.md → tasks.md。ローカルのみで管理し Git には含めない（`.gitignore` で除外）。新機能や既存機能の大きな変更に着手する際は、実装より先に `.kiro/specs/<feature-slug>/` を作成してから進めること。
- `.kiro/hooks/` — イベント駆動の自動化。**現時点では未作成**（`.claude/settings.json` も未設定）。

## 作業ログ

- 以下のいずれかを行った場合は、`logs/` 以下に「何を・なぜ行ったか」を簡潔に記録すること。
  - 要件定義・設計ドキュメント（`docs/` および `.kiro/` 配下）の新規作成・修正
  - プロジェクトのコード・設定への修正（`_kyodaishiki/` / `_main.py` 配下のファイル変更全般）
- ログは修正内容ごとに 1 ファイルを作成する。1 つのファイルに複数の修正内容を混在させないこと。
- ファイル名は `logs/<yyyymmdd_hhMMss>_<種別>_<内容がわかる名前>.md` とし、ファイル名だけで実施日時・修正の種類・内容が判別できるようにする（例: `20260916_213000_docs_initial-project-documentation.md`、コード修正なら `20260916_220000_code_fix-csm-encoding.md`）。日時は記録作成時点のローカル時刻とする。
- ログファイルは必ず Markdown 形式（`.md`）で作成する。
- 日々の作業内容を後から追跡できるようにするための記録であり、コミットメッセージや PR 説明の代わりにはしない（両方に残す）。

## トークン使用量の節約

Claude Code とのやり取りではコンテキスト消費（トークン使用量）を最小限に抑えることを常に意識する。

- ファイルを読み込む際は必要最小限のファイル・範囲のみ読み込むこと。`__shell__.py`（約 1,260 行）や `shells/select2.py`（約 1,330 行）などの大きなファイルは、まず Grep でクラス/関数の位置を特定し、該当箇所のみ `offset`/`limit` で読む。
- 直前の操作結果や会話内で既に把握できている内容を、確認目的で再度読み込まないこと。
- コードベース全体を対象とした調査では、いきなり多数のファイルを開かず、Grep/Glob で対象を絞り込んでから必要なファイルだけを読むこと。
- 出力が長大になりうるコマンドは、フィルタリングして必要な部分のみを確認すること。
- ファイルの一部を変更する場合は Write による全文書き換えではなく、Edit による差分編集を優先すること。
- 広範囲・多段階の調査はサブエージェントに委譲し、要約のみをメインの会話コンテキストに持ち込むこと。
- 同じ内容を複数のドキュメントに重複して書かない（単一情報源の原則）。

## 横断的な注意点

- リポジトリ内の Markdown ドキュメント（README.md、docs/、logs/、.kiro/）は日本語で記載すること。
- **Windows 前提のコード**である。`%USERPROFILE%` などの環境変数展開、`winshell`（ごみ箱削除）、`sjis` でのサブプロセス出力デコード、`enter.bat`/`exit.bat` といった Windows 依存箇所が多い。修正時に他 OS 対応を勝手に持ち込まない（対応する場合は spec を切る）。
- コアのインデントは**タブ**で統一されている。編集時は既存ファイルのインデント（タブ）に合わせること。`shells/` の一部にスペース混在があるが、そちらも既存に合わせる。
- コアと `shells/` は `from _kyodaishiki import __shell__` のようにパッケージ名を固定して参照している。パッケージ名 `_kyodaishiki` を変更する場合は `shells/` 全体の import も追随が必要。
- `_kyodaishiki/` はかつて独立したリポジトリ（origin: `https://github.com/tetsuya111/kyodaishiki`）だった。入れ子の `.git` は 2026-09-16 に取り除き、現在はルートリポジトリで通常ディレクトリとして追跡している。旧履歴（1 コミット）が必要な場合は上記 origin を参照する。
- 自動テストは `tests/`（pytest、現時点では `shells/llm.py` のみ対象）にある。`pytest` で実行し、実 API は呼ばずフェイクプロバイダを使う。それ以外のコードの動作確認は `python -c "import _kyodaishiki"` による import チェックと、`python _main.py` での対話シェル起動で行う。対話シェルは `%USERPROFILE%\kyodaishiki2\default_loader_home` にディレクトリを作成し、`127.0.0.1:10000`（Home サーバー）と `127.0.0.1:31103`（DNS）を bind しようとするため、確認目的で不用意に起動しない。
- 依存ライブラリは `requirements.txt` が存在せず、現在の環境に手動インストールされている（一覧は [docs/architecture.md](docs/architecture.md) の依存関係を参照）。依存を追加する場合はドキュメントも更新すること。
- `__pycache__/`、`*.pyc`、`*.swo`、`*.bu` は `.gitignore` で除外している。作業用の一時ファイルを `shells/` に置かないこと（置いた場合は仕様の根拠にしない）。
