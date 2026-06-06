# ODORIBA v0 Result Fixture Packet Design

## Purpose
建立一份 repo-side 的固定結果判讀格式（fixture packet），讓 `OperationRequestCard -> OdoribaCore -> MockTranslator -> ViewCard -> TranslationResultCard` 的正向與負向路徑在未改 runtime 的前提下可被一致驗證。

此設計專注於 v0 邊界證據：
- 只檢查最小 mock reflex arc 行為可預期性。
- 不引入真實 payload、raw data、DB 或外部系統依賴。
- 不改 `rrkal_odoriba` 程式碼。

## Current v0 evidence
目前 v0 可觀測依據為：
- `OperationRequestCard` 與 `TranslationResultCard` 之 JSON 相容輸出。
- `scripts/odoriba_v0_smoke.ps1` 的輸出欄位 (`SMOKE_REQUEST_JSON`, `SMOKE_RESULT_JSON`, `SMOKE_OK`)。
- `tests/test_smoke_serialization.py` 的既有 smoke 邊界斷言。

## Fixture packet goals
1. 將正向 / 負向 / unknown translator 結果規格化為單一「結果封包」結構。
2. 使未來可直接接上 JSON fixture 且保持可人工審核。
3. 將 exit code、status、diagnostics 與 evidence 規則明確化，避免邊界歧義。

建議欄位（固定欄位集）：
- `schema`
- `fixture_id`
- `mode`（`positive` / `negative`）
- `request_card`
- `translation_result`
- `expected_status`
- `expected_diagnostics_contains`
- `expected_evidence_refs`
- `expected_output_card_ref`
- `verified`
- `boundary_scope`

`request_card` 內建議至少含：
- `card_kind`
- `card_id`
- `requested_translator`
- `requested_view`
- `subject_ref`
- `source_card_ref`

`translation_result` 內建議至少含：
- `card_kind`
- `card_id`
- `status`
- `output_card_ref`
- `evidence_refs`
- `diagnostics`
- `request_card_ref`
- `source_card_ref`
- `translator_id`

## Positive path expected shape
- `mode`: `positive`
- `expected_status`: `success` 或 `success_with_no_evidence`
- `expected_diagnostics_contains`: 包含可接受成功訊息（例如 `Translator mock_view_v0 completed.`）
- `expected_evidence_refs`: 可以為空，但若空陣列，必須同時在 `diagnostics` 註明為 mock prototype 原因。
- `expected_output_card_ref`: `smoke-req-001::summary`
- `verified`: `false`
- `boundary_scope`: `RRKAL_odoriba_reflex_arc_v0`

執行期待：
- smoke command exit code 應為 `0`
- `status in {success, success_with_no_evidence}`
- `SMOKE_OK` 存在

## Negative path expected shape
- `mode`: `negative`
- `expected_status`: `failed`
- `expected_diagnostics_contains`: 必須含 `Unknown translator`
- `expected_output_card_ref`: 可為空字串或空值（取決於實作）
- `expected_evidence_refs`: 通常為空陣列
- `verified`: `false`

執行期待：
- smoke command exit code 應為 `0`
- `status == failed`
- `SMOKE_OK` 存在（目前 negative script 在 mock 導向下為失敗結果但 pass mode）

## Unknown translator expected shape
- `mode`: `positive` 且使用 `o1_unknown_probe` 等未知 translator
- `expected_status`: `failed`
- `expected_diagnostics_contains`: `Unknown translator`
- `expected_output_card_ref`: 通常空字串
- `expected_evidence_refs`: 可為空
- `verified`: `false`

執行期待：
- smoke command exit code 應為非零
- `status == failed`
- output 中不得含 `SMOKE_OK`

## Evidence refs rule
- `evidence_refs` 皆可為 JSON 陣列。
- v0 原型中 `evidence_refs` 可為空，前提是 `diagnostics` 提供 mock/prototype 解釋。
- 禁止將 `evidence_refs` 當作成功保證條件。

## Diagnostics rule
- positive：允許成功訊息、mock 摘要、無 evidence 說明。
- negative / unknown：必須明確提及拒絕原因（例如 Unknown translator）。
- 診斷內容應可被 fixture 的 `expected_diagnostics_contains` 命中判定。

## No-payload rule
- `OperationRequestCard` 不應包含 `payload`、`raw`、`dataframe`、`binary` 欄位。
- `request_card` 層只保留參考欄位與最小行為欄位。

## No-metadata-container rule
- 不得加入 `metadata: dict[str, Any]`。
- 可觀測欄位請列為第一級欄位，避免通用雜湊/metadata 容器。

## Forbidden expansion
- 不新增真實資料攝取/cleaning/DI/plugin/syntax island。
- 不新增 runtime integration 進入 `c_1` / `c_2` / `c_3`。
- 不加入新的 translator registry 行為。
- 不改 `CardBase`、不改 core、tests、smoke script。

## Future validation command proposal
未來驗證可直接由 fixture driver 讀取設計表內容，執行下列命令與檢查條件：
1. 以模式執行 smoke：
   - `powershell -ExecutionPolicy Bypass -File L:\vis_2_dis\scripts\odoriba_v0_smoke.ps1 -Mode positive -Translator mock_view_v0`
   - `powershell -ExecutionPolicy Bypass -File L:\vis_2_dis\scripts\odoriba_v0_smoke.ps1 -Mode negative -Translator mock_view_v0`
   - `powershell -ExecutionPolicy Bypass -File L:\vis_2_dis\scripts\odoriba_v0_smoke.ps1 -Mode positive -Translator o1_unknown_probe`
2. 以 fixture 規則比對：
   - 驗證 `SMOKE_RESULT_JSON` 是否可解析。
   - 驗證 `status`、`diagnostics`、`evidence_refs`、`output_card_ref` 與 fixture 欄位一致。
   - 驗證 positive/unknown 的 exit code 與 `SMOKE_OK` 規則。

## Boundary statement
此文件僅定義 v0 docs/evidence design。
`rrkal_odoriba` 僅保有 mock prototype 行為；repo 仍為 `vis_2_dis`；本設計不代表已具備產品可交付就緒狀態，也不代表 downstream runtime 已完成整合。
