# spec `rag-reference-control` の design.md と tasks.md を作成

- 日時: 2026-09-17 21:25
- 種別: docs（`.kiro/specs/`、Git 管理外）

## 何を行ったか

- `.kiro/specs/rag-reference-control/design.md` を新規作成した（ステータス: Draft）。
  - コマンド: 参照枚数は `/rag top [<n>]`、表示枚数は `/rag last [-n <n>]` に確定。
  - `top_k` の既定値を 15 に変更し、範囲（1〜100）の検証を `Config.__init__` に集約する。範囲外の保存値はメモリ上だけ 15 に置き換え、`config.json` へは書き戻さず、起動時に `[warn]` を表示する。
  - `/rag top` は `-5` などを docopt がオプションと解釈するため、`cmd_rag` で docopt の前に分岐して範囲を含むエラーメッセージを出す。
  - ツールは `rag_top` を新設し、既存の `rag_last` に任意の `n` を追加する。
  - `Retriever.search` のチャンク取得件数が `k * 3` であることを確認し、上限 100 枚（300 チャンク）でも問題ない旨を記載した。
- `.kiro/specs/rag-reference-control/tasks.md` を新規作成した（ステータス: Not Started）。
  - タスク1: 既定値の変更と `top_k` の検証 / タスク2: `/rag top` と状態表示 / タスク3: `/rag last -n` / タスク4: ツール定義とヘルプ / タスク5: ドキュメントと作業ログ。
  - 各完了条件に requirements.md の受け入れ基準（S1-1 など）を対応付けた。

## なぜ行ったか

- requirements.md の未解決事項がすべて解消され、利用者から設計とタスクの作成を指示されたため（`.kiro/specs/README.md` の進め方の手順 3〜5）。

## 補足

- コードは変更していない。
- tasks.md の Definition of Done では、`flake8` が本リポジトリに未導入のため対象外とした（導入は spec `automated-testing` の範囲）。
