---
name: git-iterative-commit-governance
description: >-
  在開發與文檔治理中，強制實施「一輪更新就做一輪 commit，且 commit 前必做煙霧測試、二進位防漏與文檔漂移自檢」的標準安全提交與迭代治理技能。
---

# Git 迭代提交與煙霧自檢安全治理技能 (Git Iterative Commit & Smoke Test Governance Skill)

## Overview
本技能規範了在跨 Agent 協同開發與文檔治理過程中，每當完成一輪實質性更新，便立即進行 Git 本地提交與遠端推送的標準化流程。
其核心目標是：**強制實施「煙霧測試 (Smoke Test)」、「二進位大檔案防護檢查」與「文檔漂移自檢 (Docs Drift Check)」作為提交的硬性攔截前置門檻**，從物理與流程根源防範帶病代碼、`.npz` 二進位 Payload 檔案污染遠端公開代碼庫，或是「改了代碼卻忘記更新對應文檔」的 Docs Drift 行為，確保代碼庫與治理文檔的高度一致性與安全性。

## Dependencies
* 專案內 Ingestion 安全驗證器或煙霧測試腳本（例如：`reference_python/validate_renderer_skin_asset.py`）
* 本地 Git 環境與對應遠端公開倉庫連線設定

## Quick Start
在支援本技能的專案（如 `vis_2_dis`）根目錄下，可使用專屬輔助腳本 `safe_iteration_commit.py` 極速啟動：

```bash
# 1. 執行煙霧測試自檢，確認程式碼功能正常
python3 ./reference_python/safe_iteration_commit.py smoke

# 2. 自動暫存變更、執行煙霧自檢、防漏校驗與文檔漂移自檢，無誤後進行 Commit 提交
python3 ./reference_python/safe_iteration_commit.py commit -m "feat: 您的繁體中文 commit 說明"

# 3. 若有極特殊情況確無文檔需要更新，可使用 --skip-drift 參數跳過文檔對齊檢查
python3 ./reference_python/safe_iteration_commit.py commit -m "refactor: 極微小調整" --skip-drift

# 4. 將變更推送至遠端公開倉庫的 main 分支
python3 ./reference_python/safe_iteration_commit.py push
```

## Utility Scripts (CLI 輔助腳本指令)
本技能的輔助工具 `safe_iteration_commit.py` 整合了以下四大核心安全攔截門檻，供 Agent 與開發者一鍵執行：

### 1. `smoke` (煙霧測試探測與執行)
* **行為**：自動讀取並執行專案根目錄 `asset.json` 中 `"smoke_test_command"` 所定義的測試指令。若未定義，則預設尋找並執行 `reference_python/validate_renderer_skin_asset.py` 驗證器。
* **判定標準**：測試指令必須以 exit code 0 退出才算通過。任何非 0 退出碼將被直接判定為 **SMOKE FAILED**，強硬阻斷後續的提交流程。

### 2. `commit` (防禦型安全提交閉環)
* **參數**：
  - `-m, --message` (繁體中文的 commit 說明訊息，必填)。
  - `--skip-drift` (跳過文檔漂移自檢，選填)。
* **自動化執行步驟**：
  1. **測試攔截 (Smoke Hook)**：自動調用 `smoke` 子指令。若煙霧測試未通過，立即拒絕提交並報錯中斷。
  2. **自動暫存 (Auto-Stage)**：執行 `git add .` 將所有變更（排除 `.gitignore` 中配置的檔案）加入暫存區。
  3. **防漏校驗 (Leak Defense)**：利用 `git diff --cached --name-only` 讀取暫存區，嚴格攔截任何後綴為 `.npz` 的二進位大數據 Payload 檔案，且限制單一文字或代碼檔案大小。若發現漏網之魚，立即拒絕提交並回退。
  4. **文檔漂移自檢 (Docs Drift Prevention)**：判斷暫存區內若包含實體代碼檔案（`*.py`, `*.js`, `*.ts`, `*.html`, `*.css`）的更新，則**強制要求**暫存區中必須同時包含至少一個治理文檔（`*.md`, `*.csv`）的變更。若代碼變更但無文檔變更，則強硬阻斷提交，除非傳入 `--skip-drift`。
  5. **正式提交 (Git Commit)**：前述校驗完全通過後，正式執行 `git commit -m "<說明>"`，將這輪更新打包落實。

### 3. `push` (遠端同步推送)
* **行為**：確保本地預設分支名稱命名為 `main`，並將最新提交的變更同步推送至遠端 `origin` 的 `main` 分支。

## Common Mistakes (常見工程陷阱)
1. **未在 asset.json 配置 `"smoke_test_command"`**：導致腳本找不到對應的測試而降級為預設探測，建議在專案初期明確指定。
2. **改了代碼卻忘記更新對應文檔**：這是最常見的文檔漂移錯誤。Docs Drift Check 會強硬攔截此行為。請在每次修改代碼時，同步在 README、AGENT_HANDOFF、DEVELOPMENT_LOG 等治理文檔中進行記錄。
3. **暫存區含有未被 .gitignore 排除的二進位 Payload**：若發生此錯誤，應修正專案的 `.gitignore` 檔案（例如加入 `*.npz`），並執行 `git rm --cached <檔案路徑>` 清除暫存區，然後重新執行提交。
4. **Commit 說明使用非繁體中文**：請嚴格遵循 Ruruka 專案文檔治理守則，所有提交訊息與代碼註解必須 100% 採用繁體中文撰寫。
