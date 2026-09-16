# 初期ドキュメント整備（CLAUDE.md / README.md / docs/ / .kiro/steering）

- 日時: 2026-09-16 21:36
- 種別: docs

## 何をしたか

- `CLAUDE.md` を新規作成。`C:\Users\USER\projects\community_sns\CLAUDE.md` の構成（日本語、ドキュメント索引、`.kiro/` ワークフロー、作業ログ、トークン節約、横断的注意点）を踏襲し、本プロジェクト（単一 Python パッケージ、Windows 依存、入れ子 `.git`、テストなし）に合わせて書き換えた。
- `README.md` を「# kyodaishiki_card」1 行から、概要・動作環境・起動方法・最小限の使い方・ドキュメント一覧へ書き換えた。
- `docs/requirements.md`（要件定義書）、`docs/architecture.md`（構成・データモデル・ファイル形式・ネットワーク・拡張機構）、`docs/cli.md`（シェル階層ごとのコマンドリファレンス）を新規作成。
- `.kiro/steering/{product,tech,structure}.md` が community_sns の内容のままだったため、本プロジェクトの内容に置き換えた。

## なぜ

- 作者による要件書・構成ドキュメントが存在せず、`_kyodaishiki/` のコード（約 13,000 行）を読まないと全体像が掴めない状態だったため、コードから逆算した要件と構成を文書化した。
- `.kiro/steering/` が別プロジェクトの内容を指しており、Claude Code が誤った前提（Django + Next.js）で作業する恐れがあった。

## 補足

- 要件定義書はコードからの逆算であり、「未確定」「既知の課題」として区別した箇所がある。実装と乖離を見つけた場合は `docs/` 側を修正すること。
- コードは一切変更していない。
