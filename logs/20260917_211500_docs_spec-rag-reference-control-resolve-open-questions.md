# spec `rag-reference-control` の未解決事項を解消

- 日時: 2026-09-17 21:15
- 種別: docs（`.kiro/specs/`、Git 管理外）

## 何を行ったか

- `.kiro/specs/rag-reference-control/requirements.md` の未解決事項 4 件について、利用者の決定を要件に反映し、未解決事項を「なし」にした。
  - 既存 Home の `top_k: 5`: 自動移行は行わない。`main` の `config.json` は利用者が 15 に変更済み（`top_k: 15` を確認）。Non-Goals と制約・前提条件に明記。
  - 文字数上限 `context_max_chars`: 既定値 8000 を据え置く。Non-Goals と制約・前提条件に明記。
  - 参照枚数の上限: 100 枚。ストーリー1 の基準 2・5 を「1 以上 100 以下」に変更し、`config.json` の値が範囲外のときは警告して 15 枚を用いる基準 9 を追加。用語集にも範囲を追記。
  - コマンド名: design.md で確定する（要件の対象外）。

## なぜ行ったか

- design.md に進む前に解決すべき疑問点について利用者から回答があり、要件を確定させるため。

## 補足

- コードは変更していない。次の工程は design.md の作成。
