# Odoriba v0 TranslatorRegistry Preimplementation Gate

## 前言

此文件規定 Odoriba v0 的 TranslatorRegistry 在下一階段只做文件化的行為邊界，不做實作升級、不做整合擴展。

## Canonical registry purpose

- 透過 `translator_id` 明確指派（explicit dispatch）
- 對應到本地 mock translator 映射
- 由 `OdoribaCore` 統一接收並回傳 result 邊界

## Allowed registry shape

- 本地 in-memory 映射（dictionary）
- 明確註冊（explicit registration）
- 確定性查找（deterministic lookup）
- 未知 id 走失敗拒絕路徑（fail-fast）
- 仍由 `OdoribaCore` 回傳 `TranslationResultCard` 邊界

## Rejected interpretations

- 自動探索式註冊或載入
- 依賴注入式容器式決策
- 外掛式自動載入機制
- 語法島式啟用流程
- 動態 import
- 跨 repo 的 translator 載入
- 基於未授權資料載荷欄位群的分流邏輯
- 基於未驗證原始資料輸入的轉譯決策

## future test matrix（建議）

1. 已知 translator：`translator_id='mock_view_v0'` 走 dispatch 成功
2. 未知 translator：查無 key，進入拒絕結果
3. 重複 translator id 行為預案：預期 determinism/唯一鍵規格確認
4. registry 不可 import `RRKAL_project` / `rrkal-visual-compressor` / `RRKAL_displaytools`
5. translator 輸出仍必須經由 `OdoribaCore` result 邊界

## Non-goals

- 不新增實際 registry 實作
- 不加自動解析器
- 不加入依賴注入式容器
- 不加入外掛式自動載入機制
- 不加動態匯入流程
- 不做語法島式啟用流程
- 不加入未授權資料載荷欄位群（包含未驗證原始資料輸入）
- 不加入未受約束的通用 metadata 倉格
- 不認定 repo rename/跨域整合完成

## Boundary statement

Odoriba v0 仍是 mock-only local reflex arc。
`rrkal_odoriba` 目前於 `vis_2_dis` 內部測試域運作；
registry 僅允許本地明確映射，不得作為 runtime 整合能力。
