# `_kyodaishiki/` パッケージと `_main.py` をルートリポジトリに取り込み

- 日時: 2026-09-16 21:55
- 種別: code

## 何をしたか

- `_kyodaishiki/` 配下にあった入れ子の `.git`（origin: https://github.com/tetsuya111/kyodaishiki、1 コミット）を取り除き、`_kyodaishiki/` と `_main.py` をルートリポジトリで通常ディレクトリ／ファイルとして追跡するようにした。
- 作業用ファイル（`shells/a`, `a.html`, `a.py`, `a_.py`, `h`, `vlc-help.txt`, `auhs3_util.py.bu`, `.link.py.swo`, `__server__.py.bu`）と `shells/_xvideos.py`, `shells/select2_gui.py` を削除した状態で取り込んだ。
- `.gitignore` を追加（`__pycache__/`, `*.pyc`, `*.swo`, `*.swp`, `*.bu`）。
- CLAUDE.md / README.md / docs / .kiro/steering の「入れ子 `.git`」「作業用ファイル」に関する記述を取り込み後の状態に合わせて更新した。

## なぜ

- 入れ子の `.git` があると git が `_kyodaishiki/` をサブモジュール参照として記録し、clone 先でコードが取得できないため。
- 旧リポジトリの履歴は origin に push 済みで失われない。

## 補足

- Python コード自体の変更はない（旧リポジトリの未コミット変更をそのまま取り込んでいる）。
