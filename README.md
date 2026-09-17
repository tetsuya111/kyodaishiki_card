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

AI 対話シェル（`llm`）を使う場合はさらに以下が必要です。

```
pip install anthropic voyageai chromadb
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

## AI 対話シェル（`llm`）

カードを RAG（Voyage AI 埋め込み + Chroma）で参照しながら Claude と対話する子シェルです。実装は `_kyodaishiki/shells/llm.py`。

1. 環境変数を設定する: `ANTHROPIC_API_KEY`（または `ANTHROPIC_AUTH_TOKEN`）と `VOYAGE_API_KEY`。
2. 拡張 Home シェル（`shells/augment_hs*`）で以下を実行する（Home の `enter.bat` に書いておくと自動化できます）。

```
path append C:\Users\USER\kyodaishiki2\code\_kyodaishiki
path import shells.llm
alias llm shells.llm
```

3. `llm` で対話シェル（プロンプト `ai>`）に入る。`/` で始まる行がコマンド、それ以外は LLM への発話です。

```
$llm
ai>/rag add notes              # DB "NOTES" のカードを RAG に登録
ai>/rag search 京大式カード     # ベクトル検索
ai>京大式カードの利点は？        # 関連カードを添えて Claude に質問
ai>/rag top 30                 # 対話で参照するカードの枚数を変更（1〜100、既定 15）
ai>/rag last -n 3              # 直前の応答で参照したカードの先頭 3 件
ai>notes のカード一覧を見せて    # LLM がコマンドを提案 → y/n で許可して実行
ai>/help
ai>/quit
```

シェルを起動せずに 1 回だけ実行することもできます（PowerShell / cmd から）。

```
python -m _kyodaishiki.shells.llm /rag ls
python -m _kyodaishiki.shells.llm "京大式カードの利点は？"
```

設定は `<home>/_llm/config.json`、システムプロンプトは `<home>/_llm/system_prompt.txt`、対話履歴は `<home>/_llm/history/` に保存されます。コマンド一覧は [docs/cli.md](docs/cli.md) を参照してください。

## テスト

開発用依存をインストールし、リポジトリルートで `pytest` を実行します。テストは一時ディレクトリ上のフェイクプロバイダで動作し、実 API・ネットワーク・`%USERPROFILE%` 配下のデータには触れません。

```
pip install pytest flake8
pytest
flake8 --ignore=W191,E501,E128,E126,W503,E101 _kyodaishiki/shells/llm.py tests
```

現時点でテストがあるのは `llm` シェル（`tests/test_llm_shell.py`）のみです。

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
├── tests/              # pytest（pytest.ini でルートを pythonpath に追加）
├── .kiro/steering/     # プロダクト前提（Claude Code 向け）
├── logs/               # 作業ログ
├── CLAUDE.md
└── README.md
```

`_kyodaishiki/` はかつて独立したリポジトリ（`https://github.com/tetsuya111/kyodaishiki`）でしたが、現在はこのリポジトリで直接追跡しています。
