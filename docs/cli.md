# CLI リファレンス — kyodaishiki

各シェルの `Usage:` 文字列（`_kyodaishiki/_util.py` の `Docs` クラスおよび各シェルモジュール）から起こしたコマンド一覧。コマンド名は大文字小文字を区別しない。構成は [architecture.md](architecture.md)、要件は [requirements.md](requirements.md) を参照。

---

## 起動コマンド（`python _main.py`）

```
kyodaishiki (-q <query>) [(-d <dname>)] [(--home <homeid>)] [(--db <dbid>)]
kyodaishiki home <dname>
kyodaishiki db <dname>
kyodaishiki [(-d <dname>)]
```

| 形式 | 動作 |
|---|---|
| 引数なし | Loader シェル（`=`）を開く。`-d` で Loader ディレクトリを指定 |
| `-q "<query>"` | Home（既定 `MAIN`）の DB（既定 `MAIN`）に対してクエリを 1 回実行して終了 |
| `home <dname>` | ディレクトリを `HomeTagDB` として開き Home シェル（`$`）へ |
| `db <dname>` | ディレクトリを `TagDB` として開き DB シェル（`>>`）へ |

## 共通コマンド（すべてのシェル）

| コマンド | 別名 | 説明 |
|---|---|---|
| `quit` | `q`, `exit` | シェルを抜ける |
| `help` | `h`, `-h`, `--help` | ヘルプ表示 |
| `exec file <fname>` | `ex` | ファイル内のクエリを 1 行ずつ実行 |
| `map <query_f> <args>...` | | `<args>` の各要素（カンマ区切りで複数値）を `{0}`,`{1}`... に代入して繰り返し実行 |
| `map stdin <query_f>` | | 標準入力の各行を引数として繰り返し実行 |
| `xargs <args>...` | | 標準入力 1 行を末尾引数に追加して実行 |
| `sh <command>...` | `shell` | OS コマンドを実行して出力表示 |

引数の区切りは空白。`"..."` / `'...'` で空白を含む引数を渡せる。

### BaseShell2 以上（Loader、拡張 Home など）

| コマンド | 説明 |
|---|---|
| `alias <command> <query>...` | エイリアス定義（引数なしで一覧） |
| `alias rm <command>` | エイリアス削除 |
| `ls` | 子シェル（`CHILD_SHELL` 属性を持つ読み込み済みモジュール）一覧 |
| `clean` | 開いている子シェルを閉じる |
| `<module_name> [args...]` | 子シェルを起動、または子シェルに 1 クエリを実行 |

### BaseShell3 以上（拡張 Home `augment_hs*`）

| 記法 | 説明 |
|---|---|
| `<query> > <file>` | 出力をファイルに上書き（`NULL` で破棄） |
| `<query> >> <file>` | 出力をファイルに追記 |
| `<query> \| <query2>` | 出力を `<query2>` の標準入力に渡す |
| `<query> \|\| <query_f>` | 出力の各行を空白分割し `{0}`,`{1}`... に代入して `<query_f>` を実行 |
| `<query> > <child_shell>` | 出力を子シェルのクエリとして実行 |

ディレクトリ内の `alias.txt` を起動時に読み込む。

## Loader シェル（プロンプト `=`）

| コマンド | 説明 |
|---|---|
| `ls` | Home 一覧 |
| `load <homeid>` (`lo`) | Home シェルへ |

## Home シェル（プロンプト `$`）

```
help [(-a|--all)] [(-c <command>)]
ls
select <dbid> [(-u <userid>)]
server start <dbid>
server stop <dbid>
server
append <dbid> <tags>...
remove [(-t <tags>)] [(-D <dbid>)]
remove tot [(-t <tag>)]
search [(-t <tags>)] [(-D <dbid>)] [(-u <userid>)] [(-a|--all)] [(-p <pMode>)]
list tot [<tag>]
list (t|tag) [<tag>]
csm write [(-d <dname>)]
csm append [(-d <dname>)] [(-O|--override)]
csm search [(-t <tags>)] [(-m <memo>)] [(-d <dname>)]
dns (on|off)
dns
connect <host> <dbid>
```

| コマンド | 説明 |
|---|---|
| `ls` (`l`) | DB 一覧 |
| `select <dbid>` (`se`) | DB シェルへ。`*` ワイルドカード可、最初に一致した DB を開く。`-u <userid>` で DNS 解決した他ユーザーの DB に接続 |
| `append <dbid> <tags>...` (`a`, `ap`) | DB を作成して Home に登録 |
| `remove -t <tags> / -D <dbid>` (`rm`) | DB を削除（ディレクトリも削除） |
| `remove tot [-t <tag>]` | Home の TOT を削除 |
| `search` (`s`) | DB 検索。`-p T` タグ表示、`-p S` 公開状態表示、`-p A` 両方。`-a` で `__` 始まりの DB も表示。`-u <userid>` で他ユーザーの Home を検索 |
| `list tot [<tag>]` / `list tag [<tag>]` | Home の TOT / タグ一覧 |
| `server start\|stop <dbid>` (`ser`) | DB サーバーの起動／停止（ワイルドカード可）。引数なしで R/W 許可ユーザー表示 |
| `dns on\|off` / `dns` | DNS サーバーの開閉／状態 |
| `connect <host> <dbid>` (`co`) | 他ホストの DB にクライアントシェル（`>>>`）で接続 |
| `csm write\|append\|search` | Home レベルの CSM 入出力 |
| その他 | 未知のコマンドは `select <コマンド名>` として扱う |

## DB シェル（プロンプト `>>`）

```
id
search  [(-t <tags>)] [(-m <memo>)] [(-p <pMode>)] [-r|--random] [-o <output>]
list tot [<tag>]
list (t|tag) [<tag>]
write tot
write
remove tot [<tag>]
remove [(-t <tags>)] [(-m <memo>)]
csm search [(-t <tags>)] [(-m <memo>)] [(-d <dname>)]
csm write [(-d <dname>)]
csm append [(-d <dname>)] [-O|--override]
clean
```

| コマンド | 説明 |
|---|---|
| `id` | DB の ID を表示 |
| `search` (`s`) | `-m` メモ正規表現、`-t` タグ論理式（カンマ区切りで AND、TOT 再帰展開あり）。`-p` は M/C/T/D/A の組み合わせ（既定 M）。`-r` でランダム順、既定は日付昇順 |
| `@<tag> [args]` | `search -t <tag> [args]` の省略形 |
| `write` (`w`) | 対話入力でカード追加（Memo / Comment / Tag、各項目は空行で終了）。環境変数 `WRITETAGS` を自動付与 |
| `write tot` | 対話入力で TOT 追加（Name / Tag） |
| `list tag [<tag>]` (`l`) | タグとカード数（正規表現絞り込み、カード数昇順） |
| `list tot [<tag>]` | TOT 一覧 |
| `remove` (`rm`) | 条件一致カード削除。条件なしは全削除確認 |
| `remove tot [<tag>]` | 名前が `<tag>`（括弧付き `(A)` を含む）に完全一致する TOT を削除。引数なしは全削除確認 |
| `csm write [-d <dname>]` | 全カード・TOT を `.csm` ファイルに書き出し（既定 `%USERPROFILE%\Desktop\csmFiles`） |
| `csm append [-d <dname>] [-O]` | `.csm` ファイル群を取り込み |
| `csm search` | 条件一致カードの `.csm` パスを表示 |
| `clean` (`cl`) | `.csm` 経由で DB を再構築し `data.txt` の不要領域を除去 |

### pMode

| 文字 | 表示項目 |
|---|---|
| `M` | Memo |
| `C` | Comment |
| `T` | Tags |
| `D` | Date |
| `A` | すべて（Home シェルでは `T`+`S`） |
| `S` | （Home のみ）公開中か否か |

### タグ論理式

| 記法 | 意味 |
|---|---|
| `A&&B` | AND |
| `A\|\|B` | OR |
| `-A` | NOT |
| `(A\|\|B)&&-C` | 括弧 |
| `IDEA.*` | 既存タグに対する正規表現。複数一致は OR に展開 |

## クライアントシェル（プロンプト `>>>`）

`connect` / `select -u` で接続した DB サーバーに対し、`search` / `list tot|tag` / `write [tot]` / `csm` を DB シェルと同じ構文で受け付け、クライアント経由でサーバーに問い合わせて結果を表示する。サーバー側（`CardHandler`）が解釈するプロトコルコマンド:

```
search (af|asfile) [(-m <memo>)] [(-t <tags>)] [(-c <comment>)]
search [(-m <memo>)] [(-t <tags>)] [(-c <comment>)]
tag [(-t <tag>)]
tot [(-t <tag>)]
vim (l|list) [(-m <memo>)] [(-t <tags>)] [(-c <comment>)] [(-n <number>)]
write <csmText>
append <csms>...
```

## `_path` 子シェル（プロンプト `#`、拡張 Home のみ）

```
append file <pathFile>
append <path>
import file <modulesFile>
import (pkg|package) [(-a|--all)] <dname>
import dir <dname>
import <module_name>
set <key> <value>
set [<key>]
```

| コマンド | 説明 |
|---|---|
| `append <path>` / `append file <f>` | `sys.path` に追加（ファイル指定は 1 行 1 パス） |
| `import <module>` / `import dir <d>` / `import file <f>` | モジュールを import。`AuHSShell` を持つモジュールは以降コマンドとして使える |
| `import pkg <dname> [-a]` | パッケージを import。`-a` で配下の全モジュールをエイリアス登録 |
| `set <key> <value>` / `set [<key>]` | 環境変数の設定／一覧（正規表現で絞り込み） |

## 拡張 DB シェル（`shells/select2.py` 系）— 参考

`loader.conf` で拡張 Home を指定した場合、DB シェルは `select2.DBShell` などに置き換わり、以下のような拡張コマンドが加わる（詳細は各モジュールの `Docs` クラスを参照）。

```
search [(-t <tags>)] [(--nt <noTags>)] [(-m <memo>)] [(--mm <lowUpMemo>)] [(--em <escapedMemo>)]
       [(-c <comment>)] [(-a <all_text>)] [(-F <from>)] [(-U <until>)] [(-u <userid>)] [(-D <dbid>)]
       [(--pn|--printNot)] [(-p <pMode>)] [(-r|--random)]
search rec (t|bytag) [(--dp <depth>)] [(--tn <tag_n>)] <searchArgs>...
search (n|not) ...
list tot [<tag>] [(-a|--all)] [(-r|--random)]
list (t|tag) (s|search) [(-r|--random)] [<searchArgs>...]
write (w|word) | write (l|list)
append tag [(-t <tags>)] [(-m <memo>)] [(-F <from>)] [(-U <until>)] <tagsToAppend>...
append csv <fname> [(-t <tags>)] [(-O|--override)]
remove tag [(-t <tags>)] [(-m <memo>)] <removedTags>...
alter [(-t <tags>)] [(-m <memo>)] [--tmp]
number [(-t <tags>)] [(-m <memo>)]
copy <srcid> <dstid> [(-O|--override)]
dump <dbid> [(-t <tags>)] [(-m <memo>)] [(-d <dname>)]
backup home [(-d <dname>)] [--rm-csm]
rename <srcid> <dstid>
vim [(-m <memo>)] [(-d <dname>)] [(-r|--random)]
```
