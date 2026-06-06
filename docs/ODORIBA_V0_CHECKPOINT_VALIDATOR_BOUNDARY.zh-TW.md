# Odoriba v0 Checkpoint Validator Boundary Index

## 目標與邊界

此文件記錄 Odoriba v0 checkpoint 與 checkpoint validator 的最小驗證邊界，供後續接力 agent 快速理解「可驗證項目、禁止訊號、輸出格式」。

這個階段僅涵蓋 mock-local prototype：

- repo 名稱仍為 `vis_2_dis`
- 套件命名空間為 `rrkal_odoriba`
- 僅驗證本機 checkpoint / fixture / smoke 的最小迴路
- 不可視為可交付產品、不可視為整合完成、不可視為 repo 已完成更名

## 驗證對象

- `scripts\odoriba_v0_checkpoint.ps1`
- `scripts\validate_odoriba_v0_checkpoint.py`
- `tests` 中的 checkpoint/fixture/smoke regression 測試

## Checkpoint JSON 欄位邊界

`odoriba_v0_checkpoint.ps1 -Json` 會輸出 JSON，validator 重點欄位如下：

- `schema`
- `status`
- `checkpoint_passed`
- `pytest_passed`
- `fixture_validation_passed`
- `fixture_schema_validation_passed`
- `positive_smoke_passed`
- `negative_smoke_passed`
- `repo_rename`
- `cross_repo_integration`
- `core_changed`
- `smoke_script_changed`
- `boundary`

### 成功條件（validator 視角）

- `schema == odoriba_v0_checkpoint_v1`
- `status == passed`
- `checkpoint_passed is True`
- `pytest_passed is True`
- `fixture_validation_passed is True`
- `fixture_schema_validation_passed is True`
- `positive_smoke_passed is True`
- `negative_smoke_passed is True`
- `repo_rename is False`
- `cross_repo_integration is False`
- `core_changed is False`
- `smoke_script_changed is False`

## 禁止視為完成之訊號（False readiness / blocked signals）

以下欄位只要出現 `True`，即代表超出本輪邊界（不得解讀為完成）：

- `repo_rename`
- `cross_repo_integration`
- `core_changed`
- `smoke_script_changed`

文件中不使用下列語句或其等價含義：

- 產品可用
- 整合完成
- repo 更名完成

## Human output 邊界

`odoriba_v0_checkpoint.ps1` 非 JSON 模式輸出 key=value 文字行，主要欄位：

- `pytest_passed`
- `fixture_validation_passed`
- `fixture_schema_validation_passed`
- `positive_smoke_passed`
- `negative_smoke_passed`
- `repo_rename`
- `cross_repo_integration`
- `core_changed`
- `smoke_script_changed`
- `checkpoint_passed`

## Negative mutation（validator in-memory）

`validate_odoriba_v0_checkpoint.py` 僅做 in-memory mutation 測試，不改變實際 checkpoint 行為。每個 mutation 都從合法 baseline `deepcopy` 後只改一個欄位，其餘欄位保留。

1) `repo_rename = True`
2) `cross_repo_integration = True`
3) `core_changed = True`
4) `smoke_script_changed = True`
5) required pass flag 變為 `False`：
   - `pytest_passed`
   - `fixture_validation_passed`
   - `fixture_schema_validation_passed`
   - `positive_smoke_passed`
   - `negative_smoke_passed`
6) `checkpoint_passed = False` 並維持 `status = passed`（衝突情境）

任何變異後若未被檢出，即代表邊界檢核失效。

## 遞迴與邊界控制

- 避免 checkpoint runner 展開自我呼叫。
- 可使用 `ODORIBA_CHECKPOINT_RECURSION_GUARD` 做重入防護。
- 本文件與本輪實作不新增 checkpoint 再嵌套 checkpoint。

## evidence command 對照

- `py -3 -B scripts\validate_odoriba_v0_checkpoint.py`
- `py -3 -B scripts\validate_odoriba_v0_checkpoint.py --self-test-negative`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\odoriba_v0_checkpoint.ps1 -Json`

## 邊界結論

本輪維持 v0 mock local checkpoint 邊界，不包含：

- c_1 / c_2 / c_3 runtime integration
- payload/raw/dataframe/binary 內容欄位
- `generic metadata container`（未受約束的通用 metadata 字典逃逸口）
- DI / plugin / async queue / network IO / DB / manifest pipeline

關聯合約索引：

- [ODORIBA_V0_CHECKPOINT_CONTRACT_INDEX.zh-TW.md](/L:/vis_2_dis/docs/ODORIBA_V0_CHECKPOINT_CONTRACT_INDEX.zh-TW.md)
