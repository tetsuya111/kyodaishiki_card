# 要件定義書 — kyodaishiki

本書は既存コード（`_kyodaishiki/` パッケージ）を読み解いて逆算した要件定義である。作者による正式な要件書は存在しないため、「実装から読み取れる要件」を確定要件として記述し、意図が不明確な箇所や実装が不完全な箇所は「未確定」「既知の課題」として区別している。

関連ドキュメント: [architecture.md](architecture.md)（構成・データモデル）、[cli.md](cli.md)（コマンド一覧）。

---

## 1. 背景と目的

- 梅棹忠夫『知的生産の技術』の「京大式カード」（1 枚 1 情報のカードをタグや索引で整理・再配列する手法）を、テキストファイルと対話型シェルで再現する。
- 紙のカードでは困難な「タグの論理式による横断検索」「タグ同士の階層化（TOT）」「複数カード群（DB）の束ね（Home）」「ネットワーク越しの共有」を提供する。
- ターゲットは作者本人（単一ユーザー、Windows 環境）。汎用製品としての配布は想定していない。

## 2. 用語定義

| 用語 | 意味 |
|---|---|
| カード（CSM） | Memo / Comment / Tags / Date の 4 要素からなる情報単位。ID は Memo の Adler-32 ハッシュ（`zlib.adler32`）。`.csm` ファイル（`memo\n\ncomment\n\ntag1,tag2\n\ndate`）としても入出力できる。 |
| タグ | カードに付ける分類語。内部では常に大文字に正規化される。 |
| タグ論理式 | `A&&B`（AND）、`A\|\|B`（OR）、`-A`（NOT）、`( )`（括弧）で構成する式。正規表現にマッチする既存タグへの展開も行う。 |
| TOT（Tag of Tags） | 「名前タグ → 子タグ群」の対応。タグの階層・同義関係を表し、検索時に再帰展開される。特別タグ `TAG_OF_TAG` を持つカードとして `.csm` 化できる。 |
| DB | 1 つのディレクトリに対応するカード群。`data.txt`（本文）、`card.txt`（カード索引）、`tag.txt`（タグ→カード）、`tot.txt`（TOT）で永続化される。`TagDB`（既定）と `CardDB` の 2 系統がある。 |
| Home | 複数の DB を束ねる上位 DB。DB 自体を「dbid をメモ、分類語をタグ」とするカードとして管理する。Home 自身も DB と同じファイル形式で永続化される。 |
| Loader | 複数の Home を切り替えるブートローダ相当。`loader.conf` で Home ごとの読み込みモジュールを指定できる。 |
| Home サーバー / DB サーバー | Home と DB をそれぞれ TCP で公開するサーバー。Home サーバーは dbid から DB サーバーのポートを返す。 |
| DNS | ユーザー ID ⇔ ホスト（IP）の対応表を返す簡易ネームサーバー（`dns.txt`）。 |
| userid | DNS に登録される利用者識別子。`server.conf` の読み書き権限判定にも使う。 |

## 3. 想定ユーザーと利用シナリオ

- **ユーザー**: 作者本人。CLI に慣れており、Vim・バッチファイル・正規表現を日常的に使う。
- **主要シナリオ**
  1. 思いついたことや読書メモを `write` で 1 枚ずつカード化し、タグを付ける。
  2. `search -t <論理式>` / `search -m <正規表現>` でカードを引き出し、並べ替え（日付順/ランダム）て読み返す。
  3. タグが増えたら `write tot` で階層化し、上位タグ 1 つで配下のカードをまとめて検索する。
  4. テーマごとに DB を分け、Home で `search -t` して該当 DB を見つけて `select` する。
  5. DB を `csm write` で `.csm` ファイル群に書き出してバックアップ・別 DB へ `csm append` で取り込む。
  6. Home をサーバーとして起動し、別マシンから `connect <host> <dbid>` でカードを検索する。

## 4. 機能要件

### FR-1 カード管理（DB シェル）

| ID | 要件 |
|---|---|
| FR-1.1 | 対話入力（Memo → Comment → Tag、各項目は空行で終了）でカードを追加できる。日付は入力時刻を自動付与する。環境変数 `WRITETAGS`（カンマ区切り）があればタグに自動追加する。 |
| FR-1.2 | メモの正規表現（`-m`）とタグ論理式（`-t`、カンマ区切りで AND）でカードを検索できる。 |
| FR-1.3 | 検索結果の表示項目を `-p` で選択できる（M=Memo、C=Comment、T=Tag、D=Date、A=全部）。既定は Memo のみ。 |
| FR-1.4 | 検索結果は日付昇順で表示する。`-r` でランダム順にできる。 |
| FR-1.5 | メモ／タグ条件に一致するカードを削除できる。条件なしの場合は全削除の確認を求める。 |
| FR-1.6 | タグ一覧（正規表現で絞り込み可）をカード数の昇順で表示できる。 |
| FR-1.7 | `@<tag>` を `search -t <tag>` の省略形として扱う。 |
| FR-1.8 | 同一メモのカードは重複追加しない（`--override` 指定時のみ置換）。 |
| FR-1.9 | `clean` で DB を `.csm` 経由で再構築し、削除済みカードの残骸を `data.txt` から除去できる。 |

### FR-2 タグ論理式と TOT

| ID | 要件 |
|---|---|
| FR-2.1 | タグは `&&` / `\|\|` / `-`（先頭）/ `()` で論理式を構成できる。 |
| FR-2.2 | 論理式中のタグが既存タグ集合に対する正規表現として複数一致する場合、それらの OR に展開する。 |
| FR-2.3 | `write tot` で「名前 → 子タグ群」の TOT を追加できる。名前が `A&&B` のような複合式の場合、構成タグ A・B それぞれの TOT に `A&&B` を子として登録する。 |
| FR-2.4 | タグ検索時に TOT を再帰的に展開し、名前タグの検索で子タグを持つカードも対象にする（循環は探索済み集合で打ち切る）。 |
| FR-2.5 | `list tot [<tag>]` で TOT を一覧でき、`remove tot [<tag>]` で削除できる（引数なしは全削除の確認）。 |
| FR-2.6 | TOT は `TAG_OF_TAG` タグを持つ CSM（Comment 1 行目 `*名前`、以降 `-子タグ`）として `.csm` ファイルに書き出し／読み込みできる。 |

### FR-3 CSM ファイル入出力

| ID | 要件 |
|---|---|
| FR-3.1 | `csm write [-d <dname>]` で DB の全カードと TOT を `<hash>.csm` ファイルとして書き出す。既定の出力先は `%USERPROFILE%\Desktop\csmFiles`。 |
| FR-3.2 | `csm append [-d <dname>] [-O]` でディレクトリ内の `.csm` を読み込み、カードと TOT を DB に取り込む。`-O` で同一 ID を上書きする。 |
| FR-3.3 | `.csm` 読み込み時は文字コードを自動判定（chardet）し、日付が不正な場合は空として扱う。 |
| FR-3.4 | `csm search` で、DB の検索条件に一致するカードに対応する `.csm` ファイルパスを表示する。 |

### FR-4 DB 管理（Home シェル）

| ID | 要件 |
|---|---|
| FR-4.1 | `append <dbid> <tags>...` で DB を作成し、Home にカードとして登録する。dbid は大文字化され、同名ディレクトリが作られる。 |
| FR-4.2 | `ls` で DB 一覧を表示する。 |
| FR-4.3 | `search [-t <tags>] [-D <dbid>] [-p <pMode>] [-a]` で DB をタグ／dbid 正規表現で検索する。`__` で始まる dbid は `-a` 指定時のみ表示する。`-p T` でタグ、`-p S` で公開中か否かを併記する。 |
| FR-4.4 | `select <dbid>` で DB シェルに入る。dbid は `*` をワイルドカードとするパターンで指定でき、最初に一致した DB を開く。 |
| FR-4.5 | Home シェルで未知のコマンドを入力した場合は `select <コマンド名>` として扱う。 |
| FR-4.6 | `remove -t <tags>` / `remove -D <dbid>` で DB を Home から削除し、ディレクトリも削除する。 |
| FR-4.7 | Home 自身も TOT を持ち、`list tot` / `remove tot` で操作できる。 |
| FR-4.8 | Home の `csm write` / `csm append` で Home レベルの CSM 入出力ができる。 |

### FR-5 Home 管理（Loader）

| ID | 要件 |
|---|---|
| FR-5.1 | 引数なし起動で Loader シェルが開き、`ls` で Home 一覧、`load <homeid>` で Home シェルに入る。 |
| FR-5.2 | `MAIN` という Home が存在しない場合は自動生成する。 |
| FR-5.3 | `loader.conf` の `<homeid>:<module>[,<args>...]` 行で、Home ごとに `loadHome(dname, *args)` を提供するモジュール（`shells/augment_hs3` など）を指定できる。`PATH:<path>` で `sys.path` 追加、`SET:<key> <value>` で環境変数設定ができる。 |
| FR-5.4 | Loader ディレクトリは既定で `%USERPROFILE%\kyodaishiki2\default_loader_home`。環境変数 `KYODAISHIKI_LOADER_HOME` で上書きできる。 |
| FR-5.5 | Home シェル起動時に環境変数 `KYODAISHIKI_HOME_DIR` / `KYODAISHIKI_HOME_ID` を設定する（拡張シェル用）。 |

### FR-6 サーバー公開と共有

| ID | 要件 |
|---|---|
| FR-6.1 | Home は TCP サーバー（`127.0.0.1:10000`）として動作できる。`loader.conf` に記載された Home は Loader 起動時に待受を開始する（自動生成された `MAIN` はソケットを bind するだけで待受しない）。`SELECT <dbid>` に DB サーバーのポートを、`SEARCH <tags>` に DB 一覧（JSON）を返す。 |
| FR-6.2 | `server start <dbid>` で DB をランダムポート（1000〜50000）の TCP サーバーとして公開し、`server stop <dbid>` で停止する。dbid はワイルドカードで複数指定できる。 |
| FR-6.3 | DB サーバーは `SEARCH` / `TAG` / `TOT` / `WRITE` / `APPEND` / `VIM` などのコマンドを受け付け、`200 <data>` / `400 <msg>` 形式で応答する。 |
| FR-6.4 | `server.conf` の `CHMOD <mode> <idfiles>...`（mode: R/W/-）と `LIMIT <n>` により、userid ごとの読み書き権限と同時接続上限を設定できる。ID ファイルは `File:<path>` 行で再帰的に include できる。既定は「全員読み取り可・書き込み不可」。 |
| FR-6.5 | 接続ごとに `server.log` に JSON 1 行（host / date / data）を追記する。 |
| FR-6.6 | `connect <host> <dbid>` で他ホストの DB に接続し、クライアントシェル（プロンプト `>>>`）で `search` / `list` / `write` / `csm` をリモート実行できる。`select <dbid> -u <userid>` で DNS 経由のホスト解決も行う。 |
| FR-6.7 | `search -u <userid> [-t <tags>]` で他ユーザーの Home に対して DB 検索できる。 |

### FR-7 DNS

| ID | 要件 |
|---|---|
| FR-7.1 | Home シェルは `127.0.0.1:31103` に簡易 DNS サーバーを用意し（起動直後は停止状態）、`dns on` / `dns off` で開閉、`dns` で状態表示する。 |
| FR-7.2 | `dns.txt`（`<id>:<host>` 行）を読み込み、`GET ID {"host":...}` / `GET HOST {"id":...}` に JSON で応答する。`POST {"id":...,"host":...}` で登録し `201` を返す（既存 ID/host との重複は無視される）。 |

### FR-8 シェル共通機能

| ID | 要件 |
|---|---|
| FR-8.1 | すべてのシェルで `q` / `quit` / `exit` で抜け、`h` / `help` でヘルプを表示する。コマンド名は大文字小文字を区別せず、多くに短縮形（`s`=search、`w`=write、`rm`=remove、`l`=list など）がある。 |
| FR-8.2 | 引数はスペース区切りで、シングル／ダブルクォートで空白を含む引数を渡せる。 |
| FR-8.3 | `exec file <fname>` でクエリを列挙したファイルを実行できる。シェルのディレクトリに `enter.bat` / `exit.bat` があれば入退室時に自動実行する。 |
| FR-8.4 | `map <query_f> <args>...`（`{0}` 置換）、`map stdin <query_f>`、`xargs <args>...`（標準入力 1 行を追加引数に）でクエリを反復実行できる。 |
| FR-8.5 | `sh <command>...` で OS のシェルコマンドを実行し、出力を表示する（`sjis` デコード）。 |
| FR-8.6 | `alias <cmd> <query>...` / `alias rm <cmd>` でエイリアスを定義・削除できる（BaseShell2 以上）。ディレクトリの `alias.txt` を起動時に読み込む（BaseShell3 以上）。 |
| FR-8.7 | BaseShell3 系のシェルでは `> <file>` / `>> <file>` / `> NULL` で出力先を変更でき、`\| <query>` で出力を別クエリの標準入力に、`\|\| <query_f>` で出力の各行を `{n}` 置換した別クエリに渡せる。`> <child_shell_name>` で子シェルへ流し込める。 |

### FR-9 非対話実行

| ID | 要件 |
|---|---|
| FR-9.1 | `python _main.py -q "<query>" [--home <homeid>] [--db <dbid>]` で、指定 Home（既定 MAIN）の指定 DB（既定 MAIN）に対して 1 クエリを実行して終了する。 |
| FR-9.2 | `python _main.py home <dname>` / `db <dname>` で任意のディレクトリを Home / TagDB として直接開ける。 |

### FR-10 拡張シェル（`shells/`）— 未確定・実験的

`shells/` 配下はコアシェルを継承した拡張であり、要件として固まっていない。実装から読み取れる範囲を列挙する。

| 領域 | 内容 |
|---|---|
| 拡張 Home（`augment_hs` / `augment_hs2` / `augment_hs3`） | BaseShell3 の機能（パイプ、alias.txt）と「子シェル」機構（`AuHSShell` クラスを持つモジュールをコマンド名として呼び出す）を Home シェルに追加する。`_path` シェル（`#`）で `sys.path` 追加、モジュール import、環境変数 set ができる。 |
| 汎用 DB 拡張（`select2` / `select3` / `index` / `util` / `_file`） | 検索条件の拡充（NOT タグ、日付範囲、コメント検索、再帰タグ検索）、タグ一括付替え、CSV 取込、DB 間コピー／マージ／バックアップ／リネーム、カード数集計、Vim 連携、SQLite による ID／かな索引など。 |
| ドメイン別（`book` / `bookmeter` / `reference_book` / `shiori` / `review` / `study` / `category` / `userid` / `link` / `picture`） | 書籍・著者・栞（しおり）・レビュー点数・学習記録・カテゴリツリー・ユーザー ID 一覧・リンク集・画像といった特定用途向けのカード型と専用コマンド。 |
| 外部サービス連携（`wikipedia` / `youtube` / `twitter` / `instagram` / `nichan` / `github` / `crawl` / `__selenium__` / `__site__`） | Wikipedia 記事や各種サイトから取得した内容をカード化するクローラ。`crawl` は他ユーザーの Home を巡回して DB をコピーする。 |
| その他（`mecab` / `upload` / `happymail` / `pcmax` / `dbutil` / `__profile__` / `__binalli__`） | 形態素解析、アップロード、ブラウザ操作シェル、DB ユーティリティ、プロフィール DB、バイナリ埋め込み。 |

## 5. 非機能要件

| 分類 | 要件 |
|---|---|
| 実行環境 | Windows 10/11、Python 3.x（3.12 で import 確認済み）。`%USERPROFILE%` 展開・`winshell`・`sjis` デコード・`.bat` 実行に依存するため他 OS は対象外。 |
| 依存 | コア: `docopt`, `winshell`, `chardet`, `colorama`, `python-dateutil`。拡張: `crayons`, `beautifulsoup4`, `requests`, `selenium`, `pykakasi`, `googletrans`。`requirements.txt` は未整備。 |
| データ保存 | すべてプレーンテキスト（UTF-8 の `data.txt` と JSON/数値行の索引ファイル）。外部 DB 不要。人間が直接編集・grep できること。 |
| 性能 | 1 DB の全データをメモリ上に保持し、検索は線形走査＋正規表現。個人利用規模（数千〜数万カード）を想定。`data.txt` は追記のみで、削除は `clean` による再構築まで残る。 |
| 同時実行 | DB 内部は `threading.Lock` で保護する。サーバーは `ThreadingMixIn` でハンドラをスレッド化し、`LIMIT` で同時処理数を制限する。 |
| セキュリティ | ローカルホスト／信頼ネットワーク前提。通信は平文 TCP、認証なし。`verify_request` は常に True を返しており、`server.conf` の権限は一部コマンドでしかチェックされない。 |
| 可搬性 | データディレクトリを丸ごとコピーすれば移行できる。`.csm` エクスポートで他ツールとも交換できる。 |
| 保守性 | 自動テストなし。コマンド構文は docopt の docstring（`Docs` クラス）が仕様書を兼ねる。 |

## 6. 制約・前提

- パッケージ名 `_kyodaishiki` は `shells/` 内で絶対 import されているため固定。
- `__shell__.py` が `%USERPROFILE%\code\kyodaishiki2` を `sys.path` に追加するなど、作者環境のパスがハードコードされている箇所がある。
- インデントはタブ。`shells/` の一部にスペース混在あり。
- `_kyodaishiki/` 配下に独立した `.git`（origin: github.com/tetsuya111/kyodaishiki）が入れ子で存在する。

## 7. 既知の課題（コードから確認できたもの）

| 課題 | 箇所 |
|---|---|
| `from . import __path__` はモジュールではなくパッケージ属性を import しており、意図した `_path` モジュールは読み込まれていない（`shells/augment_hs.py` 側で `_path` を明示 import しているため実害は限定的）。 | `_kyodaishiki/__shell__.py:7` |
| `shells/__site__.py` が存在しない外部パッケージ `myutil.site` を import している。 | `_kyodaishiki/shells/__site__.py` |
| `Index.finditer` が未 import の `re` と存在しない `self.data` 属性を参照している（未使用と思われる）。 | `_kyodaishiki/__index__.py` |
| `TOT_DB.appendCSM` が `override` 引数を `appendTOT` に渡していない。 | `_kyodaishiki/__db__.py` |
| 作業用ファイル（`shells/a`, `a.html`, `a.py`, `a_.py`, `h`, `*.bu`, `.link.py.swo`）がリポジトリに混入している。 | `_kyodaishiki/shells/` |
| `requirements.txt`、テスト、`.gitignore` が存在しない。 | ルート |

## 8. 今後の要件候補（未着手）

- `requirements.txt` / `pyproject.toml` の整備と、Windows 依存箇所の分離。
- コア（`__index__` / `__data__` / `__db__`）のユニットテスト追加。
- `shells/` の整理（現役スクリプトと廃止スクリプトの分離、作業用ファイルの除去）。
- 認証・暗号化を含むサーバー機能の見直し（現状はローカル専用として扱う）。

上記に着手する際は `.kiro/specs/<feature-slug>/` に requirements → design → tasks を作成してから実装する。
