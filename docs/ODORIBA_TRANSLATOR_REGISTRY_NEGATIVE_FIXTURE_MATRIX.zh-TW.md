# Odoriba v0 TranslatorRegistry Negative Fixture Matrix

## 目的

用於下一步實作前，先固定 Odoriba v0 的 TranslatorRegistry 負向與邊界測試語意。
本文件僅規劃，不新增實作。

## 前提

- 當前運作在 `vis_2_dis`，套件命名空間為 `rrkal_odoriba`。
- 流程維持為：`OperationRequestCard -> OdoribaCore -> mock translator -> ViewCard -> TranslationResultCard`。
- `request` 不包含未授權資料載荷欄位群，且不以未驗證原始資料輸入做分流判斷。

## 主要矩陣（規劃）

### 情境 A：已知 `translator_id` 成功路徑

- 輸入：`translator_id = mock_view_v0`
- 期望：
  - 走 mock 分派路徑
  - 形成可追溯的結果參考
  - `status` 進入成功區段（成功或同級成功態）
  - `diagnostics` 不得是失敗原因
  - 可為空的 `evidence_refs` 必須有明確補充規則（若定義此路徑）

### 情境 B：未知 `translator_id` 拒絕路徑

- 輸入：`translator_id = unknown_mock_view_v0`
- 期望：
  - 直接走拒絕路徑
  - `status = failed`
  - `diagnostics` 要明確記載找不到對應翻譯器
  - `evidence_refs` 可為空，但若空值則保留原因描述，不可無訊息成功
  - 不得誤判為成功

### 情境 C：重複 `translator_id` 決定性檢查

- 輸入：模擬重複 `translator_id` 申明
- 期望：
  - 保持既定對照查找的決定性
  - 不允許不明確覆蓋行為造成不可預期結果
  - 若重複 id 視為設計違規，需在文件/規格中明確規範拒絕或先於實作時封鎖

### 情境 D：禁止自動載入系譜

- 輸入：任一 fixture 皆只傳 `translator_id`
- 期望：
  - 僅允許明確 local mapping 查找
  - 不得出現外掛式自動載入流程
  - 不得使用動態匯入
  - 不得以外部注入式容器決定 translator
  - 不得透過跨 repository 來源補齊 translator

### 情境 E：結果邊界維持

- 輸入：以上任一路徑
- 期望：
  - 回傳皆由 `OdoribaCore` 產出結果邊界
  - 任何成功或失敗結果都以 `TranslationResultCard` 呈現
  - 不繞過核心邊界直接輸出

## 建議固定欄位（規劃）

- `schema`
- `fixture_id`
- `mode`（正向 / 負向）
- `request_card.requested_translator`（輸入參數）
- `request_card.requested_translator_ref`（結果對應翻譯器 id）
- `request_card.subject_ref`
- `translation_result.status`
- `translation_result.diagnostics`
- `translation_result.evidence_refs`
- `boundary_scope`

## 限制重申

- 不新增 registry 實作
- 不新增實際自動載入機制
- 不新增跨 repository 翻譯器匯入
- 不新增可接受通用 metadata 容器
- 不更新 `c_1 / c_2 / c_3` 整合進入邊界
