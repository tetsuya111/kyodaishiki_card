# ai-chat-shell の design.md / tasks.md を作成

- 日時: 2026-09-16 22:56
- 種別: spec

## 何をしたか

- `.kiro/specs/ai-chat-shell/design.md` を作成。主な設計判断:
  - `_kyodaishiki/shells/llm.py` に `LLMShell(BaseShell3)` と `AuHSShell` を置き、既存の子シェル機構（`sys.modules` の `AuHSShell` 属性探索 + `alias llm shells.llm`）で接続する。絶対 import のみ使い、`shells.llm` / `_kyodaishiki.shells.llm` の両方で import 可能にする。
  - 対話用 LLM と埋め込みモデルを `LLMProvider` / `EmbeddingProvider` で抽象化。実装は Claude（`claude-opus-5`、`messages.stream`、system に `cache_control`、`thinking` 省略）と Voyage AI（既定 `voyage-4-large`、`input_type` を document / query で使い分け）。
  - ベクトル DB は Chroma `PersistentClient`（`<home>/_llm/chroma/`、cosine）。1 レコード = 1 チャンク、メタ情報に dbid / card_id（`sha1(memo)`）/ content_hash / embed_model を持ち、差分登録と DB 絞り込みに使う。台帳は `registry.json`。
  - チャンク分割は `count_tokens` ベース（既定 1000 トークン）、段落 → 行 → 句点 → 文字数、オーバーラップなし（連結で原文復元）。
  - 対話は毎回検索 → `<cards>` ブロックをユーザーメッセージに前置 → 履歴には発話のみ残す。既定システムプロンプトを定義。
  - 履歴は `<home>/_llm/history/*.jsonl`。非対話は `python -m _kyodaishiki.shells.llm`（`HomeTagDB` で開き、ソケットを bind しない）。
  - 代替案（numpy 自作、LanceDB / sqlite-vec、contextual chunking、`-q` 拡張など）と不採用理由、リスク（Chroma の Windows 導入、API 仕様変更）を記載。
- `.kiro/specs/ai-chat-shell/tasks.md` を作成。13 タスク（依存導入検証 → 設定 → プロバイダ → チャンカー → ベクトルストア/登録 → 検索 → 対話ループ → RAG 統合 → 履歴 → 子シェル統合 → 非対話エントリ → ヘルプ → ドキュメント）を 4 マイルストーンに分け、各タスクに設計・要件の対応箇所、検証可能な完了条件、見積り、依存を記載。
- 設計で決めた Voyage AI の既定モデル（`voyage-4-large`）を requirements.md のストーリー1 に反映し、未解決事項を「なし」にした。

## なぜ

- requirements.md の未解決事項がすべて決定され、設計に進める状態になったため。
- Voyage AI の現行モデル（voyage-4 系）と Chroma の API は WebFetch で公式ドキュメントを確認して記載した。cosine 指定の記法とサーバーサイド fallback のベータヘッダ名は実装時に再確認する項目としてタスク1 に含めた。

## 補足

- コードは変更していない。ステータスはいずれも Draft / Not Started。
