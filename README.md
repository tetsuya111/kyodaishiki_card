# kyodaishiki

京大式カード（梅棹忠夫『知的生産の技術』の情報カード法）をデジタル化した、対話型シェルベースの個人用カード管理ツールです。

「メモ」「コメント」「タグ」「日付」からなるカードをテキストファイルに蓄積し、タグの論理式や TOT（Tag of Tags：タグの階層）で横断検索します。複数のカード DB を「Home」で束ね、Home を TCP サーバーとして公開すれば別プロセス・別ホストからカードを検索できます。

## 動作環境

- Windows（`%USERPROFILE%` 展開、`winshell`、`sjis` デコードなど Windows 依存の処理を含みます）
- Python 3.12 で import 確認済み（3.x 系であれば概ね動作する想定）
- 依存ライブラリ（`requirements.txt` は未整備のため手動でインストール）

```
pip install docopt winshell chardet colorama python-dateutil
```

`_kyodaishiki/shells/` 配下の拡張スクリプトを使う場合は追加で以下が必要です。

```
pip install crayons beautifulsoup4 requests selenium pykakasi googletrans
```

## 起動方法

```
python _main.py
```

引数なしで起動すると Home Loader（プロンプト `=`）が開きます。`load main` で既定の Home（プロンプト `$`）に入り、`select <dbid>` で個別の DB シェル（プロンプト `>>`）に入ります。

```
python _main.py -q "<query>" [--home <homeid>] [--db <dbid>]   # 単発クエリ実行（既定は MAIN/MAIN）
python _main.py home <dname>                                   # 指定ディレクトリを Home として直接開く
python _main.py db <dname>                                     # 指定ディレクトリを TagDB として直接開く
```

データは既定で `%USERPROFILE%\kyodaishiki2\default_loader_home\` 配下に生成されます（環境変数 `KYODAISHIKI_LOADER_HOME` で変更可）。

## 最小限の使い方

```
=load main                 # Home "MAIN" に入る
$append notes idea,work    # DB "NOTES" をタグ idea,work 付きで作成
$ls                        # DB 一覧
$select notes              # DB シェルに入る
>>write                    # Memo / Comment / Tag を対話入力してカード追加（空行で各項目を終了）
>>search -t idea           # タグ idea を持つカードを検索
>>search -m 京大 -p mct    # メモを正規表現で検索し memo/comment/tag を表示
>>list tag                 # タグとカード数の一覧
>>q                        # DB シェルを抜ける
$q
=q
```

コマンドの全体像は [docs/cli.md](docs/cli.md) を参照してください。

## ドキュメント

- [docs/requirements.md](docs/requirements.md) — 要件定義書
- [docs/architecture.md](docs/architecture.md) — プロジェクト構成・アーキテクチャ
- [docs/cli.md](docs/cli.md) — 対話シェルのコマンドリファレンス
- [CLAUDE.md](CLAUDE.md) — Claude Code 向け作業ガイド

## リポジトリ構成

```
code/
├── _main.py            # エントリポイント
├── _kyodaishiki/       # 本体パッケージ（コア + shells/ 拡張）
├── docs/               # ドキュメント
├── .kiro/steering/     # プロダクト前提（Claude Code 向け）
├── logs/               # 作業ログ
├── CLAUDE.md
└── README.md
```

`_kyodaishiki/` 配下には独立した `.git`（origin: `https://github.com/tetsuya111/kyodaishiki`）が入れ子で存在します。
