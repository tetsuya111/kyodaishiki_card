---
inclusion: always
---

# プロダクト概要

- **名称**: kyodaishiki
- **概要**: 京大式カード（梅棹忠夫『知的生産の技術』の情報カード法）をデジタル化した、対話型シェルベースの個人用カード管理ツール。Memo / Comment / Tags / Date からなるカードをテキストファイルに蓄積し、タグ論理式と TOT（Tag of Tags）で横断検索する。
- **想定ユーザー**: 作者本人（単一ユーザー、Windows、CLI 常用）。配布は想定しない。
- **主要機能（実装済み）**: カードの追加・検索・削除、タグ論理式（`&&` / `||` / `-` / `()` / 正規表現展開）、TOT によるタグ階層化、`.csm` ファイル入出力、複数 DB を束ねる Home、Home を切り替える Loader、Home / DB の TCP サーバー公開と簡易 DNS、`shells/` 配下の拡張シェル（書籍・レビュー・クローラ等）。
- **詳細**: 要件は [docs/requirements.md](../../docs/requirements.md)、構成は [docs/architecture.md](../../docs/architecture.md)、コマンドは [docs/cli.md](../../docs/cli.md)。

新機能や既存機能の大きな変更に着手する際は、機能ごとに `.kiro/specs/<feature-slug>/` に requirements → design → tasks を作成してから実装する（現時点で specs は未作成）。
