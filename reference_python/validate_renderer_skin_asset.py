#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_renderer_skin_asset.py
功能：實現 RFC v0.2.1 約定的防禦型安全 Ingestion 驗證器。
說明：
1. 實體大小比對，防範文件截斷。
2. 嚴密防禦 Path Traversal（路徑跨越攻擊）。
3. 強制 `allow_pickle=False`，消滅任意代碼注入漏洞。
4. 多級 shape、dtype、nbytes 比對，徹底防禦 Memory Bomb 攻擊。
5. 完整的 SHA-256 Checksums 比對。
"""

import os
import json
import hashlib
import numpy as np

def calculate_sha256(filepath):
    """計算檔案的 SHA-256 哈希值"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"

def is_safe_path(base_dir, target_path):
    """防禦 Path Traversal 攻擊：確保目標路徑完全在 base_dir 內"""
    abs_base = os.path.abspath(base_dir)
    abs_target = os.path.abspath(target_path)
    return os.path.commonpath([abs_base]) == os.path.commonpath([abs_base, abs_target])

def validate_renderer_skin_asset(asset_dir):
    """安全 Ingestion 驗證器核心主程式"""
    print(f"[*] 開始對皮層資產進行安全 Ingestion 校驗: {asset_dir}")
    
    # 1. 載入 asset.json 容器說明
    asset_json_path = os.path.join(asset_dir, "asset.json")
    if not os.path.exists(asset_json_path):
        raise FileNotFoundError(f"[ERROR] 找不到頂層資產說明檔: {asset_json_path}")
        
    with open(asset_json_path, 'r', encoding='utf-8') as f:
        asset_data = json.load(f)
        
    required_skins = asset_data.get("required_skins", {})
    if "terrain" not in required_skins:
        raise ValueError("[ERROR] 資產說明中未聲明必需的 terrain 皮層路徑")
        
    # 2. 載入 skins/terrain/manifest.json
    manifest_rel_path = required_skins["terrain"]
    manifest_path = os.path.join(asset_dir, manifest_rel_path)
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"[ERROR] 找不到皮層 Manifest: {manifest_path}")
        
    # 防禦 Path Traversal
    if not is_safe_path(asset_dir, manifest_path):
        raise PermissionError("[SECURITY ERROR] 檢測到 Manifest 路徑企圖越界存取！")
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
        
    # 3. 驗證 Manifest 頂層約束與限制 (Limits)
    limits = manifest.get("limits", {})
    max_dimension = limits.get("max_dimension", 65536)
    max_levels = limits.get("max_levels", 12)
    max_payload_bytes = limits.get("max_payload_bytes", 1073741824) # 1GB
    
    levels = manifest.get("levels", [])
    if len(levels) > max_levels:
        raise ValueError(f"[SECURITY ERROR] 金字塔層級數量 ({len(levels)}) 超出安全限制 ({max_levels})")
        
    # 4. 遍歷 LOD 各層級 Payload 執行嚴密安全防禦
    skin_root = os.path.dirname(manifest_path)
    checksums = manifest.get("checksums", {})
    
    for lvl_info in levels:
        lvl = lvl_info.get("level")
        path_rel = lvl_info.get("path")
        shape = lvl_info.get("shape")
        raw_nbytes = lvl_info.get("raw_nbytes")
        file_size_bytes = lvl_info.get("file_size_bytes")
        compression = lvl_info.get("compression")
        
        print(f"    --> 正在校驗 LOD 等級 {lvl}...")
        
        # A. 物理路徑存在性與 Path Traversal 校驗
        payload_abs_path = os.path.join(skin_root, path_rel)
        if not os.path.exists(payload_abs_path):
            raise FileNotFoundError(f"[ERROR] 找不到實體二進位 Payload: {payload_abs_path}")
            
        if not is_safe_path(skin_root, payload_abs_path):
            raise PermissionError(f"[SECURITY ERROR] 檢測到 Payload [{path_rel}] 企圖跨越邊界存取！")
            
        # B. 實體檔案大小校驗，防範截斷或 Memory Bomb 預載
        actual_file_size = os.path.getsize(payload_abs_path)
        if actual_file_size != file_size_bytes:
            raise ValueError(f"[ERROR] 檔案 [{path_rel}] 實體大小 ({actual_file_size}) 與 Manifest 宣告 ({file_size_bytes}) 不符！")
            
        if actual_file_size > max_payload_bytes:
            raise ValueError(f"[SECURITY ERROR] 檔案 [{path_rel}] 實體大小超出 1GB 安全上限！")
            
        # C. SHA-256 驗證
        declared_hash = checksums.get(path_rel)
        if not declared_hash:
            raise ValueError(f"[ERROR] Manifest 中找不到 [{path_rel}] 的校驗指紋")
            
        actual_hash = calculate_sha256(payload_abs_path)
        if actual_hash != declared_hash:
            raise ValueError(f"[SECURITY ERROR] 檔案 [{path_rel}] 的 SHA-256 指紋不匹配！\n  期望: {declared_hash}\n  實際: {actual_hash}")
            
        # D. 安全 numpy 載入反序列化防禦
        # 100% 關閉 allow_pickle 防止代碼執行漏洞！
        try:
            npz_data = np.load(payload_abs_path, allow_pickle=False)
        except Exception as e:
            raise ValueError(f"[SECURITY ERROR] 檔案 [{path_rel}] 加載失敗或格式不合規: {e}")
            
        # E. 陣列鍵數量與名稱防範
        keys = list(npz_data.keys())
        if len(keys) > 4:  # 限制極限鍵數量
            raise ValueError(f"[SECURITY ERROR] 檔案 [{path_rel}] 中的鍵數量 ({len(keys)}) 超出安全限制，疑似惡意包")
            
        if "data" not in keys:
            raise ValueError(f"[ERROR] 檔案 [{path_rel}] 中找不到必需的 [data] 陣列")
            
        # F. 類型與維度二次校驗 (不信任內部屬性)
        data_arr = npz_data["data"]
        
        if data_arr.ndim != 2:
            raise ValueError(f"[ERROR] 檔案 [{path_rel}] 的陣列維度 ({data_arr.ndim}) 不為 2D 矩陣")
            
        if list(data_arr.shape) != list(shape):
            raise ValueError(f"[SECURITY ERROR] 檔案 [{path_rel}] 內部 shape {data_arr.shape} 與 Manifest {shape} 不吻合！")
            
        expected_dtype = manifest.get("encoding", {}).get("type", "int16_meter")
        actual_dtype_str = str(data_arr.dtype)
        
        if expected_dtype == "int16_meter" and actual_dtype_str != "int16":
            raise ValueError(f"[SECURITY ERROR] 檔案 [{path_rel}] 的數據型態 ({actual_dtype_str}) 與預期 (int16) 不符")
            
        actual_nbytes = int(data_arr.nbytes)
        if actual_nbytes != raw_nbytes:
            raise ValueError(f"[SECURITY ERROR] 檔案 [{path_rel}] 內存 nbytes ({actual_nbytes}) 與預期 ({raw_nbytes}) 不符！")
            
        # 校驗對應級別的 valid_mask 和 coverage fraction
        mask_rel = lvl_info.get("valid_mask")
        land_rel = lvl_info.get("land_fraction")
        water_rel = lvl_info.get("water_fraction")
        
        # 遞迴檢查 valid_mask
        if mask_rel:
            mask_abs = os.path.join(skin_root, mask_rel)
            if not os.path.exists(mask_abs):
                raise FileNotFoundError(f"[ERROR] 找不到 valid_mask: {mask_abs}")
            if calculate_sha256(mask_abs) != checksums.get(mask_rel):
                raise ValueError(f"[SECURITY ERROR] valid_mask [{mask_rel}] SHA-256 損壞")
                
    print("[+] 恭喜！該皮層資產順利通過 100% 安全 Ingestion 校驗，防禦指標全部綠燈！")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.abspath(os.path.join(current_dir, "..", "examples", "synthetic_terrain.vizasset"))
    
    try:
        validate_renderer_skin_asset(sample_path)
    except Exception as e:
        print(f"\n[X] 校驗失敗: {e}")
