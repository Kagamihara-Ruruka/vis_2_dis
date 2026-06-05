# Odoriba v0 Rejection 與 Evidence Boundary Hardening

## 目標

- 固定 v0 的拒絕路徑規則（mock translator 缺失、未知 translator）。
- 固定 no-payload 不變式。
- 固定 evidence 邊界規則：`evidence_refs` 可以為空，但前提要有 `diagnostics` 解釋原因。

## Scope（L2 mock only）

- 僅覆蓋 `rrkal_odoriba` mock reflex arc。
- 不新增欄位、不改 CardBase 欄位集。
- 不新增 DB / network / async / cache / file I/O / DI / plugin / 動態 import / syntax island。
- 不做 repo rename、也不串接 c_1 / c_2 / c_3。

## Invariant 清單

### 1) Rejection invariant

- 若 `OperationRequestCard.requested_translator` 未在 `OdoribaCore` registry 中：
  - 必須回傳 `TranslationResultCard`
  - `status == TranslationResultStatus.FAILED`
  - `output_card_ref == ""`
  - `diagnostics` 需包含拒絕原因（例如 `Unknown translator`）。

### 2) No payload invariant

- `OperationRequestCard` 不得包含：
  - `payload`
  - `raw`
  - `dataframe`
  - `binary`
- 若需要補充上下文，使用既定欄位（如 `source_card_ref`、`operation`、`target_domain`）與 `diagnostics`。

### 3) Evidence-with-diagnostics invariant

- `evidence_refs` 允許為空，但**必須**有 `diagnostics`：
  - 空 evidence 的情境可為 mock fallback / 缺少證據時的 prototype 接受路徑。
  - `diagnostics` 需記載空證據合理性，不得宣告已驗證（verified）。

### 4) Core traversal invariant

- mock translator 結果須經由 `OdoribaCore` 回傳：
  - `request_card_ref`
  - `source_card_ref`
  - `output_card_ref`
  - `translator_id`

## Test coverage expected

- `tests/test_boundary_invariants.py`
  - `test_rejection_when_translator_not_registered`
  - `test_request_card_has_no_payload_fields`
  - `test_empty_evidence_requires_diagnostics`
  - `test_translator_result_traverses_core_to_view_reference`

## 禁止項（再強化）

- 不新增 `metadata: dict[str, Any]` 通用欄位。
- 不把 `CardBase` 改為含 payload/raw/pickled payload。
- 不改寫為 product readiness / integration ready / repo rename complete 等敘述。
