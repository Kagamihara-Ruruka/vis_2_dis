#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_renderer_skin_asset.py
功能：實現 RFC v0.2.2 約定的防禦型安全 Ingestion 驗證器。
說明：
1. 實體大小精確比對，防範文件截斷與多餘數據。
2. 嚴密防禦 Path Traversal（路徑跨越攻擊），先安全判斷後再 open。
3. 強制 `allow_pickle=False`，消滅任意代碼注入漏洞。
4. 提供 validate_npz_payload() 共用校驗器，全方位檢測 elevation, valid_mask, land_fraction, water_fraction 及 minmax。
   - 支援嚴格 Keys 集合匹配：set(keys) == set(expected_keys)
   - 支援預期檔案大小 expected_file_size_bytes 的精確比對。
   - 支援對 valid_mask / land_fraction / water_fraction 進行 expected_raw_nbytes = height * width 檢查。
5. 檢查真實 source_fingerprint 是否為合法 sha256 格式。
6. 驗證 schema, kind, status, grid.row_order, bounds 等基本元數據欄位。
"""

import os
import json
import hashlib
import re
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

def validate_npz_payload(
    skin_root,
    rel_path,
    expected_keys,
    expected_dtype,
    expected_ndim,
    expected_shape,
    expected_raw_nbytes,
    expected_file_size_bytes, # 新增此參數，用於精確檔案大小校驗
    declared_checksum,
    max_payload_bytes=1073741824
):
    """防禦型 NumPy Payload 共用安全校驗器 (v0.2.2 Hardened)"""
    payload_abs_path = os.path.join(skin_root, rel_path)
    
    # 1. Path Traversal 與路徑安全校驗 (先安全校驗，再 exists)
    if not is_safe_path(skin_root, payload_abs_path):
        raise PermissionError(f"[SECURITY ERROR] 檢測到 Payload [{rel_path}] 企圖跨越邊界存取！")
        
    if not os.path.exists(payload_abs_path):
        raise FileNotFoundError(f"[ERROR] 找不到實體二進位 Payload: {payload_abs_path}")
        
    # 2. 實體檔案大小精確校驗與上限防禦 (防範截斷或 Disk Bomb)
    actual_file_size = os.path.getsize(payload_abs_path)
    if actual_file_size > max_payload_bytes:
        raise ValueError(f"[SECURITY ERROR] 檔案 [{rel_path}] 實體大小超出安全上限！")
        
    if expected_file_size_bytes is not None:
        if actual_file_size != expected_file_size_bytes:
            raise ValueError(f"[SECURITY ERROR] 檔案 [{rel_path}] 實體大小 ({actual_file_size}) 與預期值 ({expected_file_size_bytes}) 不符！")
        
    # 3. SHA-256 哈希值匹配校驗
    actual_hash = calculate_sha256(payload_abs_path)
    if actual_hash != declared_checksum:
        raise ValueError(f"[SECURITY ERROR] 檔案 [{rel_path}] 的 SHA-256 指紋不匹配！\n  期望: {declared_checksum}\n  實際: {actual_hash}")
        
    # 4. 安全 NumPy 加載限制 (allow_pickle=False 防止代碼注入)
    try:
        npz_data = np.load(payload_abs_path, allow_pickle=False)
    except Exception as e:
        raise ValueError(f"[SECURITY ERROR] 檔案 [{rel_path}] 加載失敗或格式不合規: {e}")
        
    # 5. 嚴格 Keys 集合匹配校驗
    keys = list(npz_data.keys())
    if set(keys) != set(expected_keys):
        raise ValueError(f"[SECURITY ERROR] 檔案 [{rel_path}] 的鍵集合 {set(keys)} 與預期 {set(expected_keys)} 不一致！")
            
    # 6. Dtype, Ndim, Shape 與內存 Nbytes 安全檢查 (防範 Memory Bomb)
    for k in expected_keys:
        arr = npz_data[k]
        if arr.ndim != expected_ndim:
            raise ValueError(f"[ERROR] 陣列 [{rel_path}][{k}] 維度不匹配，預期 {expected_ndim}，實際 {arr.ndim}")
            
        if expected_shape is not None:
            if list(arr.shape) != list(expected_shape):
                raise ValueError(f"[SECURITY ERROR] 陣列 [{rel_path}][{k}] 的 shape {arr.shape} 與預期 {expected_shape} 不吻合！")
                
        if expected_dtype is not None:
            actual_dtype_str = str(arr.dtype)
            if actual_dtype_str != expected_dtype:
                raise ValueError(f"[SECURITY ERROR] 陣列 [{rel_path}][{k}] 數據型態 ({actual_dtype_str}) 與預期 ({expected_dtype}) 不符")
                
        if expected_raw_nbytes is not None:
            actual_nbytes = int(arr.nbytes)
            if actual_nbytes != expected_raw_nbytes:
                raise ValueError(f"[SECURITY ERROR] 陣列 [{rel_path}][{k}] 內存 nbytes ({actual_nbytes}) 與預期 ({expected_raw_nbytes}) 不符！")
                
    return npz_data

def validate_renderer_skin_asset(asset_dir):
    """安全 Ingestion 驗證器核心主程式"""
    print(f"[*] 開始對皮層資產進行安全 Ingestion 校驗: {asset_dir}")
    
    # 1. 載入 asset.json 容器說明
    asset_json_path = os.path.join(asset_dir, "asset.json")
    
    # 先做安全路徑檢查，再 exists/open
    if not is_safe_path(asset_dir, asset_json_path):
        raise PermissionError("[SECURITY ERROR] 檢測到 asset.json 路徑越界！")
        
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
    
    # 防禦 Path Traversal (先路徑校驗，再 exists)
    if not is_safe_path(asset_dir, manifest_path):
        raise PermissionError("[SECURITY ERROR] 檢測到 Manifest 路徑企圖越界存取！")
        
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"[ERROR] 找不到皮層 Manifest: {manifest_path}")
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
        
    # 3. 驗證基本元數據欄位與格式限制
    schema = manifest.get("schema")
    if schema != "rrkal.renderer_skin_asset.v0.2.2":
        raise ValueError(f"[ERROR] 不支援的 schema 版本: {schema}")
        
    kind = manifest.get("kind")
    if kind != "terrain":
        raise ValueError(f"[ERROR] 不支援的皮層種類: {kind}")
        
    status = manifest.get("status")
    if status != "ready":
        raise ValueError(f"[ERROR] 皮層狀態非法: {status}")
        
    grid = manifest.get("grid", {})
    row_order = grid.get("row_order")
    if row_order != "south_to_north":
        raise ValueError(f"[ERROR] 不符合規格的 row_order 網格排列: {row_order}")
        
    # 驗證 bounds 的合法性
    bounds = manifest.get("bounds", {})
    if bounds.get("lat_min") != -90.0 or bounds.get("lat_max") != 90.0:
        raise ValueError(f"[ERROR] 網格緯度邊界非法: {bounds}")
        
    # 驗證 source_fingerprint 是否為合法 sha256 格式
    source_fingerprint = manifest.get("source_fingerprint", "")
    if not re.match(r"^sha256:[a-fA-F0-9]{64}$", source_fingerprint):
        raise ValueError(f"[SECURITY ERROR] 非法 source_fingerprint 格式: {source_fingerprint} (必須為 sha256: 緊跟 64 位 16 進位字元)")
        
    limits = manifest.get("limits", {})
    max_levels = limits.get("max_levels", 12)
    max_payload_bytes = limits.get("max_payload_bytes", 1073741824)
    
    levels = manifest.get("levels", [])
    if len(levels) > max_levels:
        raise ValueError(f"[SECURITY ERROR] 金字塔層級數量 ({len(levels)}) 超出安全限制 ({max_levels})")
        
    # 4. 遍歷 LOD 各層級，使用 validate_npz_payload() 執行全方位安全校驗
    skin_root = os.path.dirname(manifest_path)
    checksums = manifest.get("checksums", {})
    
    for lvl_info in levels:
        lvl = lvl_info.get("level")
        h, w = lvl_info.get("shape")
        raw_nbytes = lvl_info.get("raw_nbytes")
        file_size_bytes = lvl_info.get("file_size_bytes")
        
        print(f"    --> 正在校驗 LOD 等級 {lvl}...")
        
        # A. 驗證 elevation payload
        elev_rel = lvl_info.get("path")
        validate_npz_payload(
            skin_root=skin_root,
            rel_path=elev_rel,
            expected_keys=["data"],
            expected_dtype="int16",
            expected_ndim=2,
            expected_shape=(h, w),
            expected_raw_nbytes=raw_nbytes,
            expected_file_size_bytes=file_size_bytes, # 精確比對 elevation 檔案大小
            declared_checksum=checksums.get(elev_rel),
            max_payload_bytes=max_payload_bytes
        )
        
        # B. 驗證 valid_mask payload
        mask_rel = lvl_info.get("valid_mask")
        mask_file_size = lvl_info.get("valid_mask_file_size_bytes")
        validate_npz_payload(
            skin_root=skin_root,
            rel_path=mask_rel,
            expected_keys=["data"],
            expected_dtype="uint8",
            expected_ndim=2,
            expected_shape=(h, w),
            expected_raw_nbytes=h * w, # 驗證 expected_raw_nbytes = height * width
            expected_file_size_bytes=mask_file_size, # 精確比對 valid_mask 檔案大小
            declared_checksum=checksums.get(mask_rel),
            max_payload_bytes=max_payload_bytes
        )
        
        # C. 驗證 land_fraction payload
        land_rel = lvl_info.get("land_fraction")
        land_file_size = lvl_info.get("land_fraction_file_size_bytes")
        validate_npz_payload(
            skin_root=skin_root,
            rel_path=land_rel,
            expected_keys=["data"],
            expected_dtype="uint8",
            expected_ndim=2,
            expected_shape=(h, w),
            expected_raw_nbytes=h * w, # 驗證 expected_raw_nbytes = height * width
            expected_file_size_bytes=land_file_size, # 精確比對 land_fraction 檔案大小
            declared_checksum=checksums.get(land_rel),
            max_payload_bytes=max_payload_bytes
        )
        
        # D. 驗證 water_fraction payload
        water_rel = lvl_info.get("water_fraction")
        water_file_size = lvl_info.get("water_fraction_file_size_bytes")
        validate_npz_payload(
            skin_root=skin_root,
            rel_path=water_rel,
            expected_keys=["data"],
            expected_dtype="uint8",
            expected_ndim=2,
            expected_shape=(h, w),
            expected_raw_nbytes=h * w, # 驗證 expected_raw_nbytes = height * width
            expected_file_size_bytes=water_file_size, # 精確比對 water_fraction 檔案大小
            declared_checksum=checksums.get(water_rel),
            max_payload_bytes=max_payload_bytes
        )
        
        # E. 驗證 minmax payload (LOD 全域高程摘要)
        minmax_rel = lvl_info.get("minmax_path")
        minmax_file_size = lvl_info.get("minmax_file_size_bytes")
        validate_npz_payload(
            skin_root=skin_root,
            rel_path=minmax_rel,
            expected_keys=["min", "max"],
            expected_dtype="int16",
            expected_ndim=1,
            expected_shape=(1,),
            expected_raw_nbytes=None,
            expected_file_size_bytes=minmax_file_size, # 精確比對 minmax 檔案大小
            declared_checksum=checksums.get(minmax_rel),
            max_payload_bytes=max_payload_bytes
        )
        
        # 額外校驗 minmax 範圍元數據宣告為 global_lod_summary
        minmax_scope = lvl_info.get("minmax_scope")
        if minmax_scope != "global_lod_summary":
            raise ValueError(f"[ERROR] LOD {lvl} 的 minmax 範圍元數據宣告非法: {minmax_scope}")
        
    print("[+] 恭喜！該皮層資產順利通過 100% 安全 Ingestion 校驗，防禦指標全部綠燈！")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.abspath(os.path.join(current_dir, "..", "examples", "synthetic_terrain.vizasset"))
    
    try:
        validate_renderer_skin_asset(sample_path)
    except Exception as e:
        print(f"\n[X] 校驗失敗: {e}")
