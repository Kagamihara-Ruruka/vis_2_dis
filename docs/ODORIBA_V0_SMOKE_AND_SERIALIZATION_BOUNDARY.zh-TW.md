# ODORIBA v0 Smoke 與序列化邊界

## 目的

建立可重複、最小的本地 smoke 腳本，驗證 Odoriba v0 mock reflex arc 的核心邊界：
- Request → Core → Translator → Result
- Card 序列化輸出可被穩定比對
- 不引入整合能力、不讀寫 DB、不連網、不進行 raw data ingest

## 指令

- `pwsh -File scripts/odoriba_v0_smoke.ps1`
- 測試：
  - `pytest tests -q`
- 程式語法檢查：
  - `py_compile rrkal_odoriba modules`
- 邊界掃描：
  - UTF-8 / U+FFFD
  - 禁止 import c_1/c_2/c_3 對應套件
  - 禁止 payload/raw/dataframe/binary 欄位
  - 禁止 `metadata: dict[str, Any]`

## smoke 腳本行為

- 僅建立 `OperationRequestCard`
- 透過 `OdoribaCore((MockTranslator(),))` 進行 local mock dispatch
- 斷言輸出：
  - `request.card_kind == "OperationRequestCard"`
  - `result.card_kind == "TranslationResultCard"`
- `result.status` 僅可為 `success` / `success_with_no_evidence`（positive mode）
- `negative` mode 要求 `status == failed` 且 `diagnostics` 含有 `Unknown translator`
- positive mode 若輸出 `status == failed`，Smoke 應以非零 exit code 結束，且不輸出 `SMOKE_OK`
- `evidence_refs` 為可序列化的 list
- 印出：
  - `SMOKE_REQUEST_JSON=...`
  - `SMOKE_RESULT_JSON=...`
  - `SMOKE_OK`

## 序列化規則（v0 邊界）

- 不變更 `CardBase` 欄位集合
- 不新增 `metadata: dict[str, Any]`
- 不新增 raw payload 欄位（`payload/raw/dataframe/binary`）
- `to_json_compatible_dict()` 不變更既有語意；可被 `json.dumps` 穩定輸出

## 禁止事項（此階段）

- Repo rename
- c_1 / c_2 / c_3 跨 repo import
- DI / plugin / dynamic import / async queue / cache / syntax island
- 任何 claim ready/integration readiness
