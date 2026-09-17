# docs: `/rag top` と `/rag last -n` をドキュメントに反映

- 日時: 2026-09-17 21:45
- 種別: docs（`docs/`、`.kiro/specs/`）
- spec: `.kiro/specs/rag-reference-control/`（タスク5）

## 何を行ったか

- `docs/cli.md`: llm シェルの Usage とコマンド表に `/rag top [<n>]` を追加し、`/rag last` を `/rag last [-n <n>]` に更新した。
- `docs/requirements.md`: FR-11.10 を追加した（参照枚数のコマンド指定は 1〜100・既定 15、範囲外の保存値は警告して 15 を使用、`/rag last -n`、ツール `rag_top` / `rag_last`）。
- `.kiro/specs/rag-reference-control/`: requirements.md と design.md のステータスを Approved、tasks.md を Done にし、完了条件にチェックを入れた。テストの置き場所など、実装と異なった記述 2 点を実態に合わせた。
- `.kiro/specs/README.md`: スペック一覧の `rag-reference-control` を Done にした。

## なぜ行ったか

- コード修正（`logs/20260917_214000_code_llm-rag-top-and-last-count.md`）に合わせ、コマンドリファレンスと要件定義書を実装と一致させるため。

## 補足

- README.md と `docs/architecture.md` には `top_k` の既定値やコマンド一覧の記載が無いため、変更していない。
