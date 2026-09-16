# 3 つの要件定義（automated-testing / ai-chat-shell / requirements-txt）を作成

- 日時: 2026-09-16 22:25
- 種別: spec

## 何をしたか

- `.kiro/steering/specs/create_ai_cli.md` のメモ（大見出し 3 つ）をもとに、以下 3 つの要件定義を `.kiro/specs/<slug>/requirements.md` として作成した。
  - `automated-testing`: pytest / flake8 による自動テストと lint、`_main.py` から到達可能な全シェルのテスト、README への手順記載。
  - `ai-chat-shell`: `shells/` 配下の AI 対話シェル。LLM 指定（既定 Claude）、対話、DB カードの RAG 登録・検索、RAG を用いた QA、設定の外部化。
  - `requirements-txt`: サードパーティ import の網羅的な洗い出し、バージョン固定の `requirements.txt`、整合性テスト、README 更新。
- specs の運用ルール `.kiro/specs/README.md` と雛形 `.kiro/specs/_template/{requirements,design,tasks}.md` を、community_sns の形式を本プロジェクト向け（Django/Next.js 参照を docs/architecture.md に置換、DoD を pytest/flake8 に変更）に調整して作成した。
- 雛形が参照する `docs/requirements-best-practices.md` と `docs/design-doc-best-practices.md` を community_sns からコピーし、リンクを本プロジェクトに合わせた。
- CLAUDE.md のドキュメント一覧と `.kiro/` の説明、steering の product.md / structure.md を specs 作成後の状態に更新した。

## なぜ

- メモのままでは受け入れ基準が検証可能な形になっておらず、設計・実装に進めないため。3 件は互いに独立した機能であり、CLAUDE.md の「1 機能 = 1 スペック」の粒度に合わせて分割した。
- 3 件の間には依存（開発用依存の記載先、テストの枠組み、`anthropic` の追加）があるため、各 requirements.md の「依存関係」で相互参照している。

## 補足

- いずれもステータスは Draft。設計（design.md）に進む前に「未解決事項」の確認が必要。
- コードは変更していない。
