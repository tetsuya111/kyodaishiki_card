# プロジェクト構成・アーキテクチャ — kyodaishiki

要件は [requirements.md](requirements.md)、コマンド一覧は [cli.md](cli.md) を参照。

---

## 1. ディレクトリ構成

```
code/                               # ルートリポジトリ（branch: claude / main）
├── _main.py                        # エントリポイント: import _kyodaishiki; _kyodaishiki.main()
├── _kyodaishiki/                   # 本体パッケージ（旧 tetsuya111/kyodaishiki を取り込んだもの）
│   ├── __init__.py                 # from .__main__ import main
│   ├── __main__.py                 # CLI 引数解釈（docopt）、Loader/Home/DB の起動分岐
│   ├── __shell__.py                # 対話シェル階層（BaseShell〜HomeLoader）
│   ├── __db__.py                   # カード DB（BaseDB〜HomeTagDB）
│   ├── __index__.py                # データモデル（Index, Card, Tag, TOT, Logic）
│   ├── __data__.py                 # 文字列表現（CSM, TOT テキスト形式, Logic 文字列パーサ）
│   ├── __server__.py               # TCP サーバー/クライアント（DB サーバー, Home サーバー）
│   ├── __dns__.py                  # 簡易 DNS サーバー/クライアント
│   ├── _util.py                    # Query パーサ、コマンド/Docs 定義、ソケット受信、日付ユーティリティ
│   ├── __utils__.py                # _util の再エクスポート
│   ├── _path.py                    # AuHSShell（sys.path 追加 / import / set）
│   └── shells/                     # 拡張シェル・スクリプト群（後述）
├── docs/                           # 本ドキュメント群
├── .kiro/steering/                 # product.md / tech.md / structure.md
├── logs/                           # 作業ログ
├── CLAUDE.md
└── README.md
```

## 2. 起動フロー

```
python _main.py [args]
  └─ _kyodaishiki.__main__.main()
       ├─ docopt で引数解釈
       ├─ "home <dname>" → __db__.HomeTagDB(dname) → __shell__.HomeShell(home).start()
       ├─ "db <dname>"   → __db__.TagDB(dname)     → __shell__.DBShell(db).start()
       ├─ "-q <query>"   → HomeLoader.get(homeid).home.select(dbid) → DBShell.execQuery(query)
       └─ 引数なし       → __shell__.HomeLoader(loader_dir).start()      # プロンプト "="
                              └─ load <homeid> → HomeShell.start()       # プロンプト "$"
                                    └─ select <dbid> → DBShell.start()   # プロンプト ">>"
```

- `loader_dir` は `%USERPROFILE%\kyodaishiki2\default_loader_home`（環境変数 `KYODAISHIKI_LOADER_HOME` で上書き）。
- `HomeLoader` は `loader.conf` を読み、各 Home を `loadHome(dname, *args)` で生成する。既定は `__shell__.loadHome` = `__server__.ServerHome` + `HomeShell`。`open_server` を持つ Home は Loader 起動時点でサーバー待受を開始する。

## 3. モジュールと責務

| モジュール | 行数 | 責務 | 主要クラス／関数 |
|---|---|---|---|
| `__main__.py` | 70 | CLI エントリ | `main()` |
| `_util.py` | 486 | クエリ文字列のトークン化、コマンド別名表・docopt 文字列（`Command` / `Docs`）、ソケット受信（`recv2/recv3/recvForServer/recvall`）、`realpath`（環境変数 2 段展開）、日付変換 | `Query`, `QueryStream`, `QueryArgsStream`, `Command`, `Docs` |
| `__index__.py` | 501 | テキスト上の位置（`Index`）を使ったカード・タグ・TOT のインデックス表現と、タグ論理式の評価 | `Index`, `BaseCard`, `SimpleCard`, `Card`, `Tag`, `TOT`, `Logic`, `DB` |
| `__data__.py` | 444 | 人間可読なカード表現（`.csm`）と TOT テキスト、論理式文字列 ⇔ Index 変換 | `CSM`, `TOT`, `Logic`, `Text`, `getencoding` |
| `__db__.py` | 675 | ディレクトリ単位のカード DB。本文追記・索引・保存・検索・TOT 展開 | `BaseDB`, `TOT_DB`, `BaseCardDB`, `BaseTagDB`, `CardDB`, `TagDB`, `BaseHomeDB`, `HomeTagDB`, `getDBIDs` |
| `__shell__.py` | 1259 | 対話シェル階層。コマンド解釈、パイプ、alias、子シェル、Home/DB/Loader の各シェル | `BaseShell`, `BaseShell2`, `BaseShell3`, `DBShell`, `CSMShell(2)`, `ClientShell`, `BaseHomeShell`, `BaseServerHomeShell`, `HomeShell`, `HomeLoader` |
| `__server__.py` | 939 | TCP サーバー基盤（停止可能な `serve_forever2`）、DB サーバー、Home サーバー、クライアント、権限/ログ | `BaseDBServer`, `CardHandler`, `HomeHandler`, `ServerDB`, `ServerTagDB`, `BaseServerHome`, `ServerHome`, `BaseClient`, `Client`, `ClientU` |
| `__dns__.py` | 200 | userid ⇔ host の対応を返す簡易 DNS | `Server`, `Handler`, `Client`, `getHost`, `getID` |
| `_path.py` | 121 | 拡張 Home 用の子シェル（sys.path / import / set） | `AuHSShell` |

## 4. クラス階層

### 4.1 DB 層（`__db__` / `__server__`）

```
BaseDB                  data.txt を Text として保持。appendText / find / save
└─ TOT_DB               tot.txt。appendTOT / searchTOT / getTagIdxesRec（TOT 再帰展開）
   └─ BaseCardDB        card.txt。cards: {id: Card}。append / search / remove
      ├─ CardDB         Card（memo, comment, tagIdxes, date）を保持。タグはカード側に持つ
      └─ BaseTagDB      tag.txt。tag: {tagIdx: Tag(cardIDs)}。タグ→カードの逆引きを持つ
         ├─ TagDB       SimpleCard + tag.txt。既定の DB 実装。clean() で再構築
         └─ BaseHomeDB  カード = DB エントリ（__index__.DB）。select / append(dbid) / remove
            ├─ HomeTagDB           DBClass=TagDB（非サーバー）
            └─ BaseServerHome      + BaseDBServer（Home サーバー、DBClass=ServerTagDB）
               └─ ServerHome

ServerDB    = CardDB + BaseDBServer
ServerTagDB = TagDB  + BaseDBServer
```

### 4.2 シェル層（`__shell__`）

```
BaseShell                 execQuery の基本コマンド（quit/help/exec/map/xargs/sh）、enter.bat/exit.bat
├─ BaseShell2             alias、子シェル（sys.modules 内の CHILD_SHELL 属性を持つモジュール）
│  └─ BaseShell3          パイプ（> >> | ||）、alias.txt
├─ CSMShell / CSMShell2   csm write / append / search
├─ DBShell (">>")         search / write / list / remove / csm / clean / id / @tag
├─ ClientShell (">>>")    リモート DB へのクエリ転送
├─ BaseHomeShell ("%")    ls / search / append / remove / select / list / csm
│  └─ BaseServerHomeShell server start|stop / search -u
│     └─ HomeShell ("$")  dns on|off / select -u / connect
└─ HomeLoader ("=")       ls / load、loader.conf 読込

shells/augment_hs.HomeShell = HomeShell + BaseShell3（子シェル名 AuHSShell、echo、path alias）
shells/augment_hs2/3.HomeShell はさらに継承して機能追加
```

### 4.3 サーバー層（`__server__` / `__dns__`）

```
socketserver.BaseServer
└─ BaseServer2            serve_forever2(event): Event で停止できる selector ループ
   └─ TCPServer2 → ThreadingTCPServer2 (ThreadingMixIn)
      ├─ BaseDBServer     server.conf / user.txt / server.log、Users（R/W 権限）
      │  ├─ ServerDB, ServerTagDB       ハンドラ CardHandler
      │  └─ BaseServerHome              ハンドラ HomeHandler、serve(dbid) で ServerTagDB を子として起動
      └─ __dns__.Server   ハンドラ __dns__.Handler、dns.txt
```

## 5. データモデル

### 5.1 Index ベースの索引

DB は本文を 1 本の文字列 `data.txt` に**追記のみ**で蓄積し、カード・タグ・TOT はすべて「本文中の開始位置と長さ」（`Index(start, length)`）で表現する。同じ文字列を追記しようとした場合は既存位置を再利用するため、同一メモ・同一タグは本文中に 1 度しか現れない。

```
data.txt : "京大式カードとは...IDEAWORK..."
card.txt : [[0,12],[12,30],[[42,4],[46,4]],"2026-09-16 21:00:00"]   # CardDB 形式
           [[0,12],[12,30],"2026-09-16 21:00:00"]                    # TagDB (SimpleCard) 形式
tag.txt  : [[42,4],[[0,12],[100,8]]]                                  # Tag: tagIdx → cardIDs
tot.txt  : 42,46 50,54,-8,60,64                                       # nameGroup tagGroups（数値列）
```

- カード ID は `memoIdx`（Index）。同一メモ = 同一カード。
- `Tag.id` は `tagIdx`。`TagDB` はタグ→カード ID の逆引き（`tag.txt`）を持ち、`CardDB` はカード側に `tagIdxes` を持つ。
- `TOT` は `nameGroup`（名前側の論理式）と `tagGroups`（子タグの論理式列）。負数は論理演算子（`-1`=NOT, `-2`=AND, `-4`=OR, `-8/-16`=括弧）。

### 5.2 CSM（人間可読形式）

```
<memo>
<空行>
<comment>
<空行>
<tag1>,<tag2>,...
<空行>
<date: YYYY-MM-DD HH:MM:SS>
```

ファイル名は `<adler32(memo)>.csm`（`_util.hash` は `zlib.adler32`）。TOT は `TAG_OF_TAG` タグを持ち、comment が `*名前` + 改行区切りの `-子タグ` になる。

### 5.3 タグ論理式

文字列形式（`__data__.Logic`）: `A&&B`, `A||B`, `-A`, `(A||B)&&-C`。Index 形式（`__index__.Logic`）に変換して評価する。`Logic.expandReg` は式中の各項を既存タグ集合に対する正規表現として展開し、複数一致すれば OR に置き換える。

## 6. 永続化ファイル一覧

| ファイル | 場所 | 内容 |
|---|---|---|
| `loader.conf` | Loader ディレクトリ | `<homeid>:<module>[,<args>]`、`PATH:<path>`、`SET:<key> <value>` |
| `data.txt` | Home / DB ディレクトリ | 本文（UTF-8、追記のみ） |
| `card.txt` | 同上 | カード索引（JSON 1 行 = 1 カード） |
| `tag.txt` | 同上（TagDB / Home） | タグ→カード ID 索引 |
| `tot.txt` | 同上 | TOT（数値列 1 行 = 1 TOT） |
| `enter.bat` / `exit.bat` | シェルのディレクトリ | シェル入退室時に実行されるクエリ列（バッチではなくシェルクエリ） |
| `alias.txt` | 同上（BaseShell3 系） | `<alias> <query>...` |
| `server.conf` | Home / DB ディレクトリ | `CHMOD <R\|W\|->  <idfile>...`、`LIMIT <n>` |
| `user.txt` | 同上 | userid 一覧（`File:<path>` で include 可） |
| `server.log` | 同上 | 接続ログ（JSON 1 行） |
| `dns.txt` | Home ディレクトリ | `<userid>:<host>` |
| `*.csm` | 任意（既定 `%USERPROFILE%\Desktop\csmFiles`） | エクスポートされたカード／TOT |

既定のランタイム配置:

```
%USERPROFILE%\kyodaishiki2\
└── default_loader_home\
    ├── loader.conf
    └── MAIN\                 # Home
        ├── data.txt card.txt tag.txt tot.txt
        ├── enter.bat exit.bat alias.txt
        ├── server.conf user.txt server.log dns.txt
        └── <DBID>\           # DB
            ├── data.txt card.txt tag.txt tot.txt
            ├── enter.bat exit.bat
            └── server.conf user.txt server.log
```

## 7. ネットワーク構成

| コンポーネント | 待受 | プロトコル |
|---|---|---|
| Home サーバー（`BaseServerHome`） | `127.0.0.1:10000` | `SELECT <dbid>` → `200 <port>` / `400 main`、`SEARCH <tags>` → `200 <json>` |
| DB サーバー（`ServerTagDB`） | ランダムポート（1000〜50000） | `SEARCH` / `TAG` / `TOT` / `WRITE` / `APPEND` / `VIM` / `CSM` → `200 ...` / `400 ...` |
| DNS（`__dns__.Server`） | `127.0.0.1:31103` | `GET ID {"host":..}` / `GET HOST {"id":..}` → `200 <json>`、`POST {"id":..,"host":..}` → `201` |

クライアント（`BaseClient`）は Home サーバーに `SELECT` してポートを得てから DB サーバーへ接続する。`ClientU` は userid → DNS でホスト解決してから同様に接続する。受信は `recvall`（1MB 上限、タイムアウト付き）で行い、リクエスト／レスポンスは UTF-8 の平文。

## 8. 拡張機構（`shells/`）

- **子シェル**: `BaseShell2` は `sys.modules` 中で `CHILD_SHELL`（既定 `"ChildShell"`、拡張 Home では `"AuHSShell"`）属性を持つモジュール名をコマンドとして受け付け、`<module>(home_shell)` を生成して `start()` または `execQuery()` する。`_path` シェルの `import` コマンドでモジュールを読み込めばその場で子シェルとして使える。
- **loadHome の差し替え**: `loader.conf` で `MAIN:_kyodaishiki.shells.augment_hs3` のように指定すると、そのモジュールの `loadHome(dname, host)` が返す Home シェルが使われる。
- **主要スクリプト分類**

| 分類 | ファイル |
|---|---|
| 拡張 Home | `augment_hs.py`, `augment_hs2.py`, `augment_hs3.py`, `auhs3_util.py` |
| 汎用 DB 拡張 | `select2.py`, `select3.py`, `index.py`（SQLite 索引）, `util.py`, `_file.py`, `dbutil.py` |
| ドメイン別カード | `book.py`, `bookmeter.py`, `reference_book.py`, `shiori.py`, `review.py`, `study.py`, `category.py`, `userid.py`, `link.py`, `picture.py`, `__profile__.py` |
| 外部連携／クローラ | `crawl.py`, `wikipedia.py`, `youtube.py`, `__youtube__.py`, `twitter.py`, `instagram.py`, `nichan.py`, `github.py`, `__selenium__.py`, `__site__.py` |
| その他 | `mecab.py`, `upload.py`, `happymail.py`, `pcmax.py`, `__binalli__.py` |
| （削除済み） | 作業用ファイル（`a`, `a.html`, `a.py`, `a_.py`, `h`, `vlc-help.txt`, `*.bu`, `*.swo`）と `_xvideos.py`, `select2_gui.py` は 2026-09-16 に削除 |

## 9. 依存関係

| 種別 | パッケージ | 用途 |
|---|---|---|
| コア | `docopt` | コマンド構文解析 |
| コア | `winshell` | DB 削除時のごみ箱移動 |
| コア | `chardet` | `.csm` の文字コード判定 |
| コア | `colorama` | 端末色 |
| コア | `python-dateutil` | 相対日付 |
| 拡張 | `crayons`, `beautifulsoup4`, `requests`, `selenium`, `pykakasi`, `googletrans` | 色付きプロンプト、スクレイピング、ブラウザ操作、かな変換、翻訳 |
| 標準 | `socketserver`, `selectors`, `threading`, `json`, `pickle`, `sqlite3`, `subprocess`, `_pyio` | サーバー、索引、外部コマンド |

`requirements.txt` は未整備。作者環境（Python 3.12.6）には上記がすべてインストール済み。

## 10. 技術的負債・注意点

- Windows 依存（`%USERPROFILE%`、`winshell`、`sjis`、`.bat` 命名）。
- 作者環境のパスがハードコード（`__shell__.py` の `sys.path.append("%USERPROFILE%\\code/kyodaishiki2")`、`__main__.py` の `HOME`）。
- `data.txt` は追記のみで、削除したカードの本文は `clean` まで残る。
- 認証なし・平文通信。`verify_request` は常に許可。
- テストなし。docopt の `Usage:` 文字列が事実上の仕様。
- 既知バグは [requirements.md](requirements.md) の「既知の課題」を参照。
