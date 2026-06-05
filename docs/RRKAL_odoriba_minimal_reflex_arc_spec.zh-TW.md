# RRKAL Odoriba 最小反射弧 mock 規範（Prototype）

## 身份與範圍

- Repo 目前仍為 `vis_2_dis`，只在本地維持 prototype code path。
- 目標是實作第一版最小卡片式解譯流程：
  `OperationRequestCard → OdoribaCore → mock Translator → ViewCard → TranslationResultCard`。
- 本文件僅定義可本地執行、無持久化、非整合、非生產化行為。
- Repo rename 尚未完成，不在此任務中執行。

## 實作邊界（本輪）

- 僅新增最小 mock 元件：
  - `CardBase v0`
  - `OperationRequestCard v0`
  - `ViewCard v0`
  - `TranslationResultCard v0`
  - `OdoribaCore`
  - 明確 in-memory translator registry
  - 一個 mock translator
- 嚴禁：
  - Raw data ingest / payload 內容流入
  - c_1 / c_2 / c_3 依賴
  - DB、renderer、compressor、manifest、network、DI、plugin、async queue、persistent cache
- `RequestCard` 只作為文件語彙，正式類別只使用 `OperationRequestCard`。

## 卡片欄位（v0）

`CardBase` 必要欄位：

- `card_id`
- `card_kind`
- `schema_version`
- `producer`（卡片生產者）
- `subject_ref`（穩定語義參考，非 raw path）
- `status`
- `evidence_refs`
- `boundary_scope`

`OperationRequestCard`：

- 包含 `operation`、`source_card_ref`、`requested_view`、`target_domain`、`requested_translator` 等參考欄位。
- 不允許 payload/raw payload/dataframe/binary/render buffer 等大欄位。

`TranslationResultCard`：

- 包含 `status`、`request_card_ref`、`source_card_ref`、`translator_id`、`output_card_ref`、`diagnostics`、`evidence_refs`。
- mock 情境可出現 `evidence_refs == ()`，`diagnostics` 必須補述原因。

## 驗收建議

- `pytest tests -q` 全通過。
- 於 report-before-commit 階段，補充：
  - no forbidden imports（RRKAL_project / rrkal-visual-compressor / RRKAL_displaytools）
  - 無 payload slot
  - 無通用 metadata dict 容器（`dict[str, Any]`）
  - 無 product readiness / integration readiness / repo rename complete 的宣告
