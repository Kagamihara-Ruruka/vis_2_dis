#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
safe_iteration_commit.py
功能：跨 Agent 協同之「一輪更新一輪 commit，commit 前必做煙霧測試」的迭代提交與安全治理技能（Skill）。
說明：
1. smoke：自動讀取並優先執行 asset.json 內宣告的煙霧測試指令。
2. commit：強制執行煙霧測試，通過後自動檢查並過濾 *.npz 大檔案，確認無誤後方能執行本地 Git Commit。
3. push：安全將 main 分支推送到遠端 GitHub 倉庫。
"""

import os
import sys
import json
import subprocess
import argparse

def get_smoke_command(project_root):
    """從 asset.json 讀取煙霧測試指令，若無則預設探測"""
    asset_json = os.path.join(project_root, "asset.json")
    if os.path.exists(asset_json):
        try:
            with open(asset_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 支援從配置中讀取
            cmd = data.get("smoke_test_command")
            if cmd:
                return cmd
        except Exception:
            pass
            
    # 預設探測
    ref_val = os.path.join(project_root, "reference_python", "validate_renderer_skin_asset.py")
    if os.path.exists(ref_val):
        return f"python3 \"{ref_val}\""
        
    return None

def run_smoke_test(project_root):
    """執行煙霧測試，回傳是否通過"""
    print("[*] 步驟 1：正在啟動煙霧測試 (Smoke Test)...")
    cmd = get_smoke_command(project_root)
    if not cmd:
        print("[!] 警告: 未探測到定義的煙霧測試指令，預設判定為通過。")
        return True
        
    print(f"    --> 執行指令: {cmd}")
    try:
        # 在專案根目錄下執行煙霧指令
        res = subprocess.run(cmd, shell=True, cwd=project_root)
        if res.returncode == 0:
            print("[+] 煙霧測試完全通過 (SMOKE PASS)！")
            return True
        else:
            print(f"[🛑 煙霧測試失敗 (SMOKE FAILED)]：退出碼為 {res.returncode}")
            return False
    except Exception as e:
        print(f"[🛑 執行煙霧測試時發生異常]：{e}")
        return False

def check_binary_leak(project_root):
    """二進位數據安全治理：防範 *.npz 或大檔案被錯誤 commit"""
    print("[*] 步驟 2：正在對暫存區進行二進位大檔案防漏檢查...")
    try:
        # 取得準備提交的暫存檔案列表
        res = subprocess.run(
            "git diff --cached --name-only", 
            shell=True, 
            cwd=project_root, 
            capture_output=True, 
            text=True
        )
        if res.returncode != 0:
            print("[!] Git 暫存區讀取失敗（可能尚未執行 git add）。")
            return True
            
        staged_files = res.stdout.strip().split("\n")
        leaked_files = []
        
        for f in staged_files:
            if not f:
                continue
            # 1. 強制排除 *.npz
            if f.endswith(".npz"):
                leaked_files.append(f)
                continue
                
            # 2. 限制單一文字/代碼檔案大小不得超過 10MB
            full_path = os.path.join(project_root, f)
            if os.path.exists(full_path):
                f_size = os.path.getsize(full_path)
                if f_size > 10 * 1024 * 1024:  # 10MB
                    leaked_files.append(f"{f} (大小為 {f_size} 位元組，超出上限)")
                    
        if leaked_files:
            print("[🛑 安全紅線攔截]：發現以下暫存檔案違反了數據治理原則，已被拒絕 Commit：")
            for lf in leaked_files:
                print(f"    - {lf}")
            print("[!] 請修正 .gitignore 或是執行 'git rm --cached' 清理暫存區後重試。")
            return False
            
        print("[+] 暫存區二進位防漏檢查通過 (DATA GOVERNANCE PASS)！")
        return True
    except Exception as e:
        print(f"[🛑 執行數據防漏檢查時發生異常]：{e}")
        return False

def do_safe_commit(project_root, commit_msg):
    """執行安全 Commit"""
    if not commit_msg:
        print("[X] 錯誤: 請提供本次 commit 的中文說明訊息！")
        sys.exit(1)
        
    # 1. 煙霧測試
    if not run_smoke_test(project_root):
        print("[🛑 拒絕 Commit]：因煙霧測試失敗，已強硬攔截提交。請先修正代碼缺陷。")
        sys.exit(1)
        
    # 2. 二進位防漏檢查
    # 先將所有工作區變動 add 到暫存區（除了被 gitignore 的部分）
    print("[*] 正在暫存工作區變動...")
    subprocess.run("git add .", shell=True, cwd=project_root)
    
    if not check_binary_leak(project_root):
        print("[🛑 拒絕 Commit]：因暫存區包含二進位大檔案，已強硬攔截提交。")
        sys.exit(1)
        
    # 3. 執行 Git Commit
    print(f"[*] 步驟 3：正在執行 Git Commit...")
    cmd = ["git", "commit", "-m", commit_msg]
    res = subprocess.run(cmd, cwd=project_root)
    if res.returncode == 0:
        print(f"[+] 恭喜！本次一輪更新已安全 Commit 成功！")
    else:
        print(f"[X] Commit 失敗，Git 退出碼: {res.returncode}")
        sys.exit(res.returncode)

def do_safe_push(project_root):
    """安全推送到遠端"""
    print("[*] 正在執行遠端推送...")
    # 確保分支為 main
    subprocess.run("git branch -M main", shell=True, cwd=project_root)
    res = subprocess.run("git push origin main", shell=True, cwd=project_root)
    if res.returncode == 0:
        print("[+] 遠端 GitHub 公開倉庫推送成功！")
    else:
        print(f"[X] 推送失敗，退出碼: {res.returncode}")
        sys.exit(res.returncode)

def main():
    parser = argparse.ArgumentParser(description="Git 迭代安全提交與煙霧測試輔助工具 (Skill)")
    subparsers = parser.add_subparsers(dest="command", help="子指令")
    
    # smoke subcommand
    subparsers.add_parser("smoke", help="執行煙霧測試")
    
    # commit subcommand
    commit_parser = subparsers.add_parser("commit", help="執行煙霧與防漏校驗，無誤後進行 Commit")
    commit_parser.add_argument("-m", "--message", required=True, help="繁體中文 commit 說明訊息")
    
    # push subcommand
    subparsers.add_parser("push", help="將 main 分支安全推送遠端")
    
    args = parser.parse_code = parser.parse_args()
    project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    
    if args.command == "smoke":
        if run_smoke_test(project_root):
            sys.exit(0)
        sys.exit(1)
    elif args.command == "commit":
        do_safe_commit(project_root, args.message)
    elif args.command == "push":
        do_safe_push(project_root)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
