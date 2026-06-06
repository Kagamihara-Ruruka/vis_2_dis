# Odoriba v0 Checkpoint Contract Index

## Scope map

本索引整理 Odoriba v0 checkpoint/validator/fixture 的邊界關係，避免跨文件拼接理解錯誤。

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
- negative self-test: mutate payload in memory and assert invalid combinations are rejected
- command:
  - `py -3 -B scripts\validate_odoriba_v0_checkpoint.py`
  - `py -3 -B scripts\validate_odoriba_v0_checkpoint.py --self-test-negative`

### result fixture validator node

- validates fixture packet fields and optional smoke behavior
- required checks:
  - schema / fixture_id / mode / verified false
  - forbidden fields (`payload`, `raw`, `dataframe`, `binary`, `metadata`) blocked in request card
  - translation_result `evidence_refs` and `diagnostics` present
  - positive/negative/unknown expectations align with smoke output
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

若以上任一為 true，代表 v0 邊界未維持，不能轉為更高階接力條件。

## Scan-safe prohibited exact phrase policy

本文件與關聯文檔避免直接出現高敏掃描短語，改以替代表達:

- 非交付可用
- 非跨 repo 流程收斂完成
- 非 repo 名稱更名確認狀態

## Readability guard and separation rules

- checkpoint aggregates leaf evidence only
- validator validates output and boundary flags
- meta-test behavior is in validator self-test, not in checkpoint runner
- checkpoint must not invoke validator to call checkpoint
- no loops of checkpoint -> pytest -> validator -> checkpoint

## boundary statement

- no `c_1`, `c_2`, `c_3` runtime integration
- no payload/raw/dataframe/binary fields
- no generic metadata container
- no DI / plugin / syntax island
- no repo rename claim
- no product ready / integration ready style assertion
