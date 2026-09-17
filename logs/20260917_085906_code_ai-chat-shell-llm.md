# AI 対話シェル（shells/llm.py）を実装

- 日時: 2026-09-17 08:59
- 種別: code

## 何をしたか

- `_kyodaishiki/shells/llm.py` を新規作成（約 1,250 行）。拡張 Home シェルの子シェル `llm` として動く `LLMShell` / `AuHSShell` と、`python -m _kyodaishiki.shells.llm` の非対話エントリを実装した。
  - `/` 始まりをコマンド、それ以外を LLM への発話として扱う。`//` は `/` 始まりの発話のエスケープ。
  - 対話用 LLM（`ClaudeProvider`: anthropic SDK、`messages.stream` でストリーミング、system に prompt caching、`fallbacks="default"`）と埋め込み（`VoyageProvider`: voyageai SDK、既定 `voyage-4-large`）を `Provider` で抽象化。設定は 起動オプション > 環境変数 > `<home>/_llm/config.json` > 既定値。
  - RAG: `str(CSM)` を `count_tokens` ベースで分割（段落 → 行 → 句点 → 文字数、オーバーラップなし）し、Chroma `PersistentClient`（cosine）に DB ID・カード ID・内容ハッシュ・埋め込みモデル付きで差分登録。`/rag add|rm|ls|search|on|off|use|last`。
  - 対話: 発話ごとに検索して `<cards>` ブロックをユーザーメッセージに前置。履歴には発話のみ残す。トークン使用量の表示。
  - ツール呼び出し: シェル内コマンドをツール定義として公開し、`tool_use` ごとに等価なコマンド行を表示して y/n 許可を取る手動ループ。`/sh` `/exec` `/clear` `/quit` `/tools` は非公開。非対話では自動拒否。
  - 履歴を `<home>/_llm/history/*.jsonl` に保存し `/history ls|show|rm`。
- `tests/conftest.py`（フェイクプロバイダ、一時 Home フィクスチャ）と `tests/test_llm_shell.py`（70 件）、`pytest.ini` を追加。`pytest` 全件 pass、`flake8`（W191/E501 等を除外）違反なし。
- 依存を導入: chromadb 1.5.9、voyageai 0.5.0、pytest 9.1.1、flake8 7.3.0（anthropic 1.2.0 は導入済み）。
- ドキュメント更新: README.md（依存、`llm` の使い方、テスト）、docs/cli.md（`llm` 節）、docs/architecture.md（拡張分類、`_llm/` ファイル、依存）、docs/requirements.md（FR-11）、CLAUDE.md（テストの存在、specs はローカル管理）。

## なぜ

- `.kiro/specs/ai-chat-shell/`（requirements → design → tasks）に従った実装。設計で「実装時に確認」としていた Chroma の cosine 指定記法と Anthropic の fallback ベータヘッダは、SDK の署名・型定義で確認して design.md に反映した。

## 補足

- 実 API（Anthropic / Voyage AI）との疎通は API キー未設定のため未確認。
- メインシェルからの手動確認（`$llm`）は未実施。`AuHSShell` 経由の起動はテストで確認。
- Git Bash から `python -m ... /rag ls` を実行すると MSYS のパス変換で `/rag` が壊れる。PowerShell / cmd から実行する（docs/cli.md に記載）。
- `pip install chromadb` の際に、既存の `pyppeteer` と `pyee` / `websockets` のバージョン競合警告が出た（chromadb 側の依存更新による）。動作確認はしていない。
