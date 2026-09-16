---
inclusion: always
---

# ディレクトリ構成

```
code/
├── _main.py              # エントリポイント（_kyodaishiki.main() を呼ぶだけ）
├── _kyodaishiki/         # 本体パッケージ（入れ子の .git あり）
│   ├── __main__.py       # CLI 引数解釈と起動分岐
│   ├── __shell__.py      # 対話シェル階層（Loader / Home / DB / Client）
│   ├── __db__.py         # カード DB（TagDB / CardDB / HomeDB）
│   ├── __index__.py      # データモデル（Index / Card / Tag / TOT / Logic）
│   ├── __data__.py       # CSM 形式・論理式文字列
│   ├── __server__.py     # TCP サーバー / クライアント
│   ├── __dns__.py        # 簡易 DNS
│   ├── _util.py          # Query パーサ、Command / Docs、ユーティリティ
│   ├── _path.py          # 拡張 Home 用の子シェル
│   └── shells/           # 拡張シェル・スクリプト群（実験的）
├── docs/                 # requirements.md / architecture.md / cli.md
├── logs/                 # 作業ログ（<yyyymmdd_hhMMss>_<種別>_<内容>.md）
├── .kiro/
│   └── steering/         # 常時参照されるプロジェクトコンテキスト（このファイルを含む）
├── CLAUDE.md             # 索引。詳細は docs/ と .kiro/ を参照
└── README.md
```

## 配置の指針

- コア機能の変更は `_kyodaishiki/` 直下の該当モジュールに行う。シェルのコマンド追加は `_util.py` の `Command` / `Docs` に別名と `Usage:` を追加し、該当シェルクラスの `execQuery` に分岐を足す。
- 特定用途向けの機能（書籍管理、クローラなど）はコアに入れず `_kyodaishiki/shells/<name>.py` に置き、コアのシェルクラスを継承する。子シェルとして使う場合は `AuHSShell` クラスを定義する。
- ランタイムデータ（`data.txt` など）はリポジトリ外に生成される。リポジトリ内にコミットしない。
- 新機能に着手する際は、まず `.kiro/specs/<feature-slug>/` に requirements → design → tasks を作成してから実装に入る。
- ドキュメントの詳細情報は `docs/` に一本化し、`.kiro/steering/` や `CLAUDE.md` からはリンクのみ行う（重複させない）。
