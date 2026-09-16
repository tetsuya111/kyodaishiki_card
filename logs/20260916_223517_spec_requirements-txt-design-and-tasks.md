# requirements-txt スペックの design.md / tasks.md を作成

- 日時: 2026-09-16 22:35
- 種別: spec

## 何をしたか

- `.kiro/specs/requirements-txt/design.md` を `_template/design.md` の構成で作成した。1 ファイル + コメント区分の `requirements.txt`、`-r` で本番依存を参照する `requirements-dev.txt`、AST ベースの import 抽出テスト `tests/test_requirements.py`、対応表 `tests/dependency_map.py` という構成。未解決事項 3 点（分割の要否、`==` か `>=` か、CI）を「検討した代替案」で決着させた。
- `.kiro/specs/requirements-txt/tasks.md` を 7 タスク・4 マイルストーンに分解した。M1（依存ファイル）→ M2（テスト）→ M3（クリーン環境確認）→ M4（ドキュメント一本化）。
- 設計にあたり AST で全 `.py` の import を再走査し、requirements.md の依存表（12 件）を検証した。2 点の事実誤認を見つけ、requirements.md（requirements-txt / automated-testing の両方）を修正した。
  - `myutil` の import 元は `shells/__site__.py` ではなく `shells/bookmeter.py`。
  - `winshell` は `pywin32` を実行時に必要とするが `install_requires` で宣言していないため、`pywin32==311` を明示的に記載する必要がある（design.md の `IMPLICIT_DISTS` として扱う）。

## なぜ

- requirements.md がストーリー・受け入れ基準まで固まっており、設計と実装計画がないと着手できないため。
- automated-testing スペックと `tests/` / `pytest.ini` の所有関係が衝突しうるため、本スペックは最小設定のみ置き automated-testing 側で拡張する、と design.md に明記した。

## 補足

- ステータスは design: Draft、tasks: Not Started。コードは変更していない。
- `requirements-dev.txt` の pytest / flake8 / pytest-cov の版は現環境に未インストールのため、実装時（タスク5）に取得する。
