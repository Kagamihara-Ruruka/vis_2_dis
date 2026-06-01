---
name: git-iterative-commit-governance
description: >-
  在跨 Agent 協同開發與文檔治理中，強制實施「一輪更新就做一輪 commit，且 commit 前必做煙霧測試與二進位防漏校驗」的標準迭代提交與安全治理技能。
---

# Git 迭代提交與安全治理技能 (Git Iterative Commit Governance Skill)

## Overview
本技能規範了跨 Agent 協同開發時，每當完成一輪更新，便立即進行 Git 本地提交與遠端推送的標準化流程。
核心價值在於：**強制實施「煙霧測試 (Smoke Test)」與「二進位大檔案防護檢查」作為 Commit 的硬性攔截前置門檻**，從物理根源抹殺任何帶病代碼或 `.npz` 二進位 Payload 檔案污染遠端公開代碼庫的可能。

## Dependencies
* 本專案 Ingestion 安全驗證器：`reference_python/validate_renderer_skin_asset.py`

## Quick Start
在 `vis_2_dis` 專案根目錄下，使用 `safe_iteration_commit.py` 輔助腳本即可極速啟動此技能：

```bash
# 1. 執行煙霧測試自檢
python3 ./reference_python/safe_iteration_commit.py smoke

# 2. 強制執行「煙霧測試 -> 防漏校驗 -> 本地 Git Commit」閉環
python3 ./reference_python/safe_iteration_commit.py commit -m "feat: 您的繁體中文 commit 說明"

# 3. 推送到遠端 main 分支
python3 ./reference_python/safe_iteration_commit.py push
```

## Utility Scripts (CLI 輔助腳本指令)

本技能的 Helper 腳本 `safe_iteration_commit.py` 具備以下三大核心 subcommand 模組：

### 1. `smoke` (煙霧測試探測器)
* **行為**：自動讀取並執行專案根目錄 `asset.json`（或 `manifest.json`）中宣告的 `"smoke_test_command"`。
* **預設探測**：若未宣告，自動探測並執行本專案之安全 Ingestion 驗證器。
* **校驗紅線**：非 0 退出碼將被直接判定為 SMOKE FAILED，並強制阻斷後續 Commit 流程。

### 2. `commit` (防禦型安全提交閘道)
* **參數**：`-m, --message` (繁體中文 commit 說明訊息)。
* **行為步驟**：
  1. **SMOKE**：自動調用 `smoke` 子指令。失敗則立即阻斷。
  2. **ADD**：自動暫存工作區的所有文本與代碼變更 (`git add .`)。
  3. **CHECK**：利用 `git diff --cached --name-only` 讀取暫存區，嚴格過濾阻斷任何後綴為 `.npz` 的二進位大檔案，且單一檔案大小限制不得超過 10MB。
  4. **COMMIT**：前兩項校驗均綠燈通過後，正式執行 `git commit`。

### 3. `push` (遠端同步推送)
* **行為**：重新命名本地預設分支為 `main`，並安全推送至遠端 GitHub 公開倉庫 `origin` 的 `main` 分支。

## Common Mistakes (常見工程陷阱)
1. **忘記在 asset.json 宣告煙霧測試**：這會導致腳本自動探測預設驗證器，建議在每項新子專案中明確配置 `"smoke_test_command"`。
2. **暫存區含有未排除的二進位大檔案**：若發生此錯誤，請修正 `.gitignore`（如加上 `*.npz`）並執行 `git rm --cached <file>` 清空暫存區後重新執行。
3. **Commit 說明使用非繁體中文**：請嚴格遵循 Ruruka 專案文檔治理守則，Commit 訊息必須 100% 採用繁體中文撰寫。
