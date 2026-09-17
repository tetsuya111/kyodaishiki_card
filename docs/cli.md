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

## `llm` 子シェル（プロンプト `ai>`、拡張 Home のみ）

カードを RAG（Voyage AI 埋め込み + Chroma）で参照しながら LLM（既定 Claude）と対話する。実装は `_kyodaishiki/shells/llm.py`。

有効化: `_kyodaishiki/` を `sys.path` に置いたうえで、メインシェルでモジュールを import し、`llm` にエイリアスする。Home の `enter.bat` に書いておくと起動時に実行される。

```
path append C:\Users\USER\kyodaishiki2\code\_kyodaishiki
path import shells.llm
alias llm shells.llm
```

環境変数: `ANTHROPIC_API_KEY`（または `ANTHROPIC_AUTH_TOKEN`）、`VOYAGE_API_KEY`。設定は `<home>/_llm/config.json`、システムプロンプトは `<home>/_llm/system_prompt.txt`。

### 起動（メインシェルから）

```
llm [--llm <provider>] [--model <model>] [--embed <provider>] [--embed-model <model>] [<input>...]
```

`<input>` なしで対話シェルを開始。`<input>` があれば 1 回だけ処理して戻る（`/` 始まりはコマンド、それ以外は発話）。

### 入力の分類

| 入力 | 扱い |
|---|---|
| `/` で始まる行 | シェル内コマンド |
| `//` で始まる行 | 先頭の `/` を 1 つ除いた発話 |
| 未知の `/xxx` | エラー表示（LLM には送らない） |
| それ以外 | LLM への発話。毎回 RAG でカードを検索し、プロンプトに含めて送る |

LLM がシェル内コマンドの実行を提案した場合は、等価なコマンド行を表示して `実行しますか? (y/n)` を求める。`y` / `yes` 以外はすべて拒否。

### シェル内コマンド

```
/rag add <dbid>...
/rag (rm|remove) <dbid>...
/rag (ls|list)
/rag (s|search) [(-D <db>)] [(-n <n>)] <query>...
/rag (on|off)
/rag use [<db>]
/rag top [<n>]
/rag last [(-n <n>)]
/model
/usage
/tools (on|off)
/clear
/history (ls|list)
/history show <id>
/history (rm|remove) <id>
/help
/quit
```

| コマンド | 説明 |
|---|---|
| `/rag add <dbid>...` | DB の全カード（`str(CSM)`）を埋め込んでベクトル DB に登録。差分登録、`*` ワイルドカード可、進捗表示 |
| `/rag rm <dbid>...` | DB を RAG から削除 |
| `/rag ls` | 登録済み DB（件数・チャンク数・更新日時・埋め込みモデル）。現在のモデルと異なる行に `!` |
| `/rag search` | ベクトル検索。カード単位に集約し、全文・ヒットチャンク・スコアを表示 |
| `/rag on` / `/rag off` | 対話時の自動検索の有効／無効（`config.json` に保存） |
| `/rag use [<db>]` | 対話時の検索対象 DB を限定。引数なしで解除 |
| `/rag top [<n>]` | 対話 1 回あたりに参照するカードの枚数の表示／変更（1〜100、既定 15）。`config.json` の `top_k` に保存され、`/rag search` で `-n` を省略したときの件数にもなる |
| `/rag last [-n <n>]` | 直前の応答で参照したカード一覧。`-n` で先頭 n 件だけ表示（参照枚数の設定は変えない） |
| `/model` | 対話用 LLM と埋め込みモデル、認証情報の有無、RAG の状態（on/off・参照枚数・対象 DB） |
| `/usage` | トークン使用量（直前／セッション累計） |
| `/tools on` / `/tools off` | LLM からのコマンド提案（ツール呼び出し）の有効／無効 |
| `/clear` | メモリ上の対話履歴を破棄し、新しい履歴ファイルを開始（保存済みは残る） |
| `/history ls` / `show <id>` / `rm <id>` | `<home>/_llm/history/*.jsonl` の一覧・表示・削除 |
| `/exec` `/map` `/xargs` `/sh` `/alias` | 共通コマンド（`/` 付きで使う） |

### 非対話実行

```
python -m _kyodaishiki.shells.llm [--home-dir <dname>] [--llm <provider>] [--model <model>] [--embed <provider>] [--embed-model <model>] <input>...
```

`--home-dir` の既定は `%KYODAISHIKI_LOADER_HOME%\MAIN`。LLM が提案したコマンドはすべて自動的に拒否される。Git Bash から実行する場合は `/rag` などがパスに変換されるため、PowerShell / cmd から実行するか `MSYS_NO_PATHCONV=1` を付ける。

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
