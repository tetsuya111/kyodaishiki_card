# llm シェル: 参照枚数のコマンド指定（`/rag top`）と `/rag last -n` を実装

- 日時: 2026-09-17 21:40
- 種別: code（`_kyodaishiki/shells/llm.py`、`tests/test_llm_shell.py`）
- spec: `.kiro/specs/rag-reference-control/`（タスク1〜4）

## 何を行ったか

- `_kyodaishiki/shells/llm.py`
  - `DEFAULTS["top_k"]` を 5 から 15 に変更。`TOP_K_MIN = 1`、`TOP_K_MAX = 100` と、範囲付きの整数解釈 `parse_count(text, lo, hi=None)` を追加。
  - `Config.__init__` の末尾に `_validate_top_k` を追加。`top_k` が 1〜100 の整数（`bool` を除く）でなければメモリ上だけ 15 に置き換え、`Config.warnings` に警告文を積む。`config.json` へは書き戻さない。`warnings` は `__dict__` に直接置き、`config.json` に混入しないようにした。
  - `/rag top [<n>]` を追加（`rag_top`）。引数なしで現在値を表示、1〜100 の整数で `config.json` に保存。`-5` などを docopt がオプションと解釈するため、`cmd_rag` で docopt の前に分岐して範囲を含む `[error]` を出す。
  - `/rag last [(-n <n>)]` に変更。先頭 n 件を表示し、総数より少ないときだけ `(n / 総数 件を表示)` を出す。`-n` が不正なら `[error]` でカードは表示しない。
  - `/model` の RAG 行に `top <n>` を追加。起動時に `_warn_config` で `Config.warnings` を `[warn]` 表示。
  - ツール `rag_top` を新設し、`rag_last` に任意の `n` を追加。`Docs.HELP` を更新。
- `tests/test_llm_shell.py`
  - 既定値のアサーションを 5 から 15 に更新。
  - `TestParseCount` / `TestTopKConfig` / `TestRagTop` / `TestRagLastCount` / `TestTopKTools` を追加（70 件 → 117 件）。

## なぜ行ったか

- 参照枚数を変えるには `config.json` の手編集が必要で、既定の 5 枚では複数 DB に分散した関連カードが漏れやすかったため。利用者の決定（既定 15 枚、上限 100 枚、`context_max_chars` は据え置き、既存の保存値は自動移行しない）に従った。
- `/rag last` は参照枚数を増やすと一覧が長くなるため、表示枚数を絞れるようにした。

## 確認結果

- `python -c "import _kyodaishiki.shells.llm"`: 成功
- `python -m pytest -q`: 117 passed
- 対話シェルの手動起動による確認は未実施（ポートを bind するため）。
