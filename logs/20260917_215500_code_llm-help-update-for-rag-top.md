# llm シェル: `/help` を参照枚数まわりの修正に合わせて更新

- 日時: 2026-09-17 21:55
- 種別: code（`_kyodaishiki/shells/llm.py`、`tests/test_llm_shell.py`）と付随するドキュメント（`docs/cli.md`、`README.md`）
- spec: `.kiro/specs/rag-reference-control/`

## 何を行ったか

- `_kyodaishiki/shells/llm.py` の `Docs.HELP` を更新した。
  - `/rag search`: 「-n 省略時は /rag top の枚数」を追記。
  - `/rag top`: 「設定は保存される」を追記。
  - `/model`: 説明を「対話用 LLM と埋め込みモデル、RAG の状態（on/off・参照枚数・対象 DB）の表示」に変更。
  - `/rag top [<n>]` と `/rag last [-n <n>]` の行自体は、実装時（`logs/20260917_214000_code_llm-rag-top-and-last-count.md`）に追加済み。
- `tests/test_llm_shell.py`: `/help` の出力に上記の追記が含まれることを検証するアサーションを追加した。
- `docs/cli.md`: `/model` の説明に RAG の状態（on/off・参照枚数・対象 DB）を追記した。
- `README.md`: llm シェルの使用例に `/rag top 30` と `/rag last -n 3` を追加した。

## なぜ行ったか

- 参照枚数の実装で `/model` の表示内容と、`/rag search` の既定件数の決まり方（`/rag top` の値に従う）が利用者から見えるようになったが、ヘルプの説明が修正前のままだったため。

## 確認結果

- `python -m pytest -q`: 117 passed
