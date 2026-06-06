# Odoriba v0 Checkpoint Contract Index

## Scope map

Odoriba v0 checkpoint/validator/fixture 的驗證鏈條如下：
- checkpoint script: `scripts\odoriba_v0_checkpoint.ps1`
- checkpoint validator: `scripts\validate_odoriba_v0_checkpoint.py`
- result fixture validator: `scripts\validate_odoriba_v0_result_fixtures.py`
- fixture packet design: `docs\ODORIBA_V0_RESULT_FIXTURE_PACKET_DESIGN.zh-TW.md`
- checkpoint boundary index: `docs\ODORIBA_V0_CHECKPOINT_VALIDATOR_BOUNDARY.zh-TW.md`

## Contract chain (minimal mock flow)

Odoriba v0 在 local prototype 中固定為：

- `OperationRequestCard -> OdoribaCore -> mock translator -> ViewCard -> TranslationResultCard`
- positive path: `scripts\odoriba_v0_smoke.ps1 -Mode positive -Translator mock_view_v0`
- negative path: `scripts\odoriba_v0_smoke.ps1 -Mode negative -Translator mock_view_v0`
- unknown probe path: `scripts\odoriba_v0_smoke.ps1 -Mode positive -Translator o1_unknown_probe`

## TranslatorRegistry preimplementation gate

Odoriba v0 邊界先用文件 gate 固定 registry 行為：

- 僅允許本地明確映射（`translator_id` -> mock translator）
- deterministic lookup
- 禁止自動探索、外掛式自動載入機制、依賴注入式容器、動態 import、語法島式啟用流程
- 禁止跨 repo translator 來源
- 未知 id 走拒絕結果
- 仍由 `OdoribaCore` 維持 result 邊界輸出

參考門檻文件：`docs\ODORIBA_TRANSLATOR_REGISTRY_PREIMPLEMENTATION_GATE.zh-TW.md`

## Evidence nodes

### checkpoint node

- aggregate target:
  - `pytest` pass/fail
  - fixture validation pass/fail
  - fixture schema validation pass/fail
  - positive smoke pass/fail
  - negative smoke pass/fail
- output surfaces:
  - human mode: key=value lines
  - JSON mode: machine-readable object

### validator node

- validates checkpoint JSON schema and boundary gates
- required true:
  - schema = `odoriba_v0_checkpoint_v1`
  - status = `passed`
  - checkpoint_passed = true
  - pytest_passed = true
  - fixture_validation_passed = true
  - fixture_schema_validation_passed = true
  - positive_smoke_passed = true
  - negative_smoke_passed = true
- required false:
  - repo_rename
  - cross_repo_integration
  - core_changed
  - smoke_script_changed
  - negative self-test: mutate 驗證用負載資料並驗證無效組合會被拒絕
- command:
  - `py -3 -B scripts\validate_odoriba_v0_checkpoint.py`
  - `py -3 -B scripts\validate_odoriba_v0_checkpoint.py --self-test-negative`

### result fixture validator node

- validates fixture packet fields and optional smoke behavior
- required checks:
  - schema / fixture_id / mode / verified false
  - 在 request card 中禁止未授權資料欄位組（資料載荷欄位群）與未驗證原始資料輸入欄位
  - `translation_result` requires `evidence_refs` and `diagnostics`
  - positive / negative / unknown expectations align with smoke output
- command:
  - `py -3 -B scripts\validate_odoriba_v0_result_fixtures.py`

## JSON / human output boundary

- checkpoint JSON mode exposes:
  - schema
  - status
  - checkpoint_passed
  - pytest_passed
  - fixture_validation_passed
  - fixture_schema_validation_passed
  - positive_smoke_passed
  - negative_smoke_passed
  - repo_rename
  - cross_repo_integration
  - core_changed
  - smoke_script_changed
- checkpoint human mode exposes the same logical pass/fail key-value lines

## False readiness signals (do not read as completion)

- repo rename done
- cross-repo runtime integration done
- core changed
- smoke script changed

## Scan-safe prohibited exact phrase policy

以下字詞或語義只可在邏輯說明中使用 scan-safe 表述，避免被誤判為完成狀態或固定機制：
- 倉庫名稱更動已完成（需避免作為完成指標）
- 跨域接軌已完成（需避免作為完成指標）
- 整體產品可用性已完成（需避免作為完成指標）
- 外掛式自動載入機制（需避免作為完成指標）
- 依賴注入式容器／外掛式自動載入／動態匯入／語法島式啟用流程（需避免作為完成指標）
- 無限制 metadata 容器（需避免作為完成指標）

## Readability guard and separation rules

- checkpoint aggregates leaf evidence only
- validator validates output and boundary flags
- meta-test 行為限制在 validator self-test，不放入 checkpoint 腳本
- checkpoint 不應呼叫 validator -> checkpoint -> pytest -> validator 迴圈

## boundary statement

- no `c_1`, `c_2`, `c_3` runtime integration
- no 未授權資料載荷欄位群
- no unrestricted 通用 metadata 容器
- no repository rename claim
- no product/integration completion assertion
