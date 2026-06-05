#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspect_renderer_skin_asset.py
功能：對 TerrainSkinAsset 進行 CLI 可讀化診斷與結構性檢查。
說明：
1. 檢查並顯示 source_fingerprint 的合法性。
2. 對金字塔每一級的 elevation, valid_mask, land_fraction, water_fraction, minmax 進行實體 Checksum 與精確 file_size 吻合檢查。
3. 驗證並顯示 coverage payloads 內存符合 height * width 的 uint8 期望大小。
4. 顯示 minmax_scope 範圍宣告。
5. 當 ssim 為空值 (null) 時，顯示 terrain_ssim_not_computed。
6. 計算並顯示 LOD 數據壓縮比。
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

def inspect_renderer_skin_asset(asset_dir):
    """診斷皮層資產內容"""
    print("=" * 75)
    print(f"  [TerrainSkinAsset CLI 診斷工具 v0.2.2] - {os.path.basename(asset_dir)}")
    print("=" * 75)
    
    asset_json = os.path.join(asset_dir, "asset.json")
    if not os.path.exists(asset_json):
        print(f"[X] 錯誤: 找不到資產檔: {asset_json}")
        return
        
    with open(asset_json, "r", encoding="utf-8") as f:
        asset = json.load(f)
        
    print(f"[*] 資產 ID: {asset.get('asset_id')}")
    print(f"[*] 資產類型: {asset.get('type')}")
    print(f"[*] 建立時間: {asset.get('created_at')}")
    
    # 讀取 manifest.json
    manifest_rel = asset.get("required_skins", {}).get("terrain")
    if not manifest_rel:
        print("[X] 錯誤: required_skins 中無 terrain 皮層定義")
        return
        
    manifest_path = os.path.join(asset_dir, manifest_rel)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    skin_root = os.path.dirname(manifest_path)
    checksums = manifest.get("checksums", {})
    
    print("-" * 65)
    print("  [皮層 Manifest 參數]")
    print("-" * 65)
    print(f"  - 綱要版本: {manifest.get('schema')}")
    
    # 驗證 source_fingerprint 的合法性
    source_fingerprint = manifest.get("source_fingerprint", "")
    is_valid_fp = bool(re.match(r"^sha256:[a-fA-F0-9]{64}$", source_fingerprint))
    fp_status = "✅ 合法 SHA-256" if is_valid_fp else "🛑 非法格式 placeholder"
    print(f"  - 原始資料指紋: {source_fingerprint} ({fp_status})")
    
    print(f"  - 編碼格式: {manifest.get('encoding', {}).get('type')}")
    print(f"  - 量化步長: {manifest.get('encoding', {}).get('scale')} 米")
    print(f"  - 投影系統: {manifest.get('projection', {}).get('system')}")
    print(f"  - 行列排布 (row_order): {manifest.get('grid', {}).get('row_order')}")
    print(f"  - 行列公式: {manifest.get('grid', {}).get('lat_index_formula')}")
    print(f"  - 地理經緯邊界:")
    bounds = manifest.get("bounds", {})
    print(f"      緯度: {bounds.get('lat_min')} 至 {bounds.get('lat_max')}")
    print(f"      經度: {bounds.get('lon_min')} 至 {bounds.get('lon_max')}")
    
    print("\n  - 金字塔 LOD 層級與 Payload 完整度檢查:")
    for lvl in manifest.get("levels", []):
        lvl_num = lvl.get("level")
        h, w = lvl.get("shape")
        raw_nbytes = lvl.get("raw_nbytes")
        file_size = lvl.get("file_size_bytes")
        
        # 計算壓縮比
        comp_ratio = raw_nbytes / file_size if file_size > 0 else 0
        
        print(f"      [LOD {lvl_num}] shape=[{h}, {w}] | 內存={raw_nbytes}B | 實體={file_size}B | 壓縮比={comp_ratio:.2f}x")
        
        # 校驗各 Payload 實體檔案、Checksum 與 expected_file_size_bytes
        payloads = {
            "elevation": (lvl.get("path"), file_size, raw_nbytes),
            "valid_mask": (lvl.get("valid_mask"), lvl.get("valid_mask_file_size_bytes"), h * w),
            "land_fraction": (lvl.get("land_fraction"), lvl.get("land_fraction_file_size_bytes"), h * w),
            "water_fraction": (lvl.get("water_fraction"), lvl.get("water_fraction_file_size_bytes"), h * w),
            "minmax": (lvl.get("minmax_path"), lvl.get("minmax_file_size_bytes"), None)
        }
        
        for name, (rel_p, expected_size, expected_nbytes) in payloads.items():
            abs_p = os.path.join(skin_root, rel_p)
            if not os.path.exists(abs_p):
                print(f"        [-] {name:<15}: 🛑 檔案缺失 ({rel_p})")
                continue
                
            # Checksum 校驗
            declared_hash = checksums.get(rel_p)
            actual_hash = calculate_sha256(abs_p)
            hash_ok = (actual_hash == declared_hash)
            
            # File size 檢查
            actual_size = os.path.getsize(abs_p)
            size_ok = (actual_size == expected_size)
            
            # nbytes 期望大小檢查 (針對 valid_mask, land/water fraction = h * w)
            nbytes_status = ""
            if expected_nbytes is not None:
                # 實體載入校驗 npz
                try:
                    npz_data = np.load(abs_p, allow_pickle=False)
                    actual_nbytes = npz_data["data"].nbytes
                    if actual_nbytes == expected_nbytes:
                        nbytes_status = " | ✅ 內存符合 h*w 期望"
                    else:
                        nbytes_status = f" | 🛑 內存不匹配 (預期 {expected_nbytes}B, 實際 {actual_nbytes}B)"
                except Exception as e:
                    nbytes_status = f" | 🛑 無法讀取內存: {e}"
            
            size_label = "✅ file_size 吻合" if size_ok else f"🛑 file_size 損壞 (預期 {expected_size}B, 實際 {actual_size}B)"
            hash_label = "✅ Checksum 吻合" if hash_ok else "🛑 Checksum 損壞"
            
            print(f"        [+] {name:<15}: {hash_label} | {size_label}{nbytes_status}")
            
        # 顯示 minmax 範圍與性質
        minmax_scope = lvl.get("minmax_scope", "unknown")
        print(f"        [+] minmax_scope   : 範圍性質 (scope): {minmax_scope}")
        
    # 讀取 review.json
    review_path = os.path.join(asset_dir, "review.json")
    if os.path.exists(review_path):
        with open(review_path, "r", encoding="utf-8") as f:
            review = json.load(f)
        print("-" * 65)
        print("  [Review Packet 實體量化誤差憑證]")
        print("-" * 65)
        fidelity = review.get("source_fidelity", {})
        print(f"  - 均方根高程誤差 (RMSE): {fidelity.get('rmse_meters'):.6f} 米")
        print(f"  - 平均絕對誤差 (MAE): {fidelity.get('mae_meters'):.6f} 米")
        print(f"  - P95 最大高程誤差: {fidelity.get('p95_absolute_error_meters'):.6f} 米")
        print(f"  - 最大量化絕對誤差 (Max): {fidelity.get('max_absolute_error_meters'):.6f} 米")
        
        ssim = fidelity.get("ssim")
        if ssim is None:
            print("  - 結構相似度 (SSIM): terrain_ssim_not_computed")
        else:
            print(f"  - 結構相似度 (SSIM): {ssim:.6f}")
            
        print(f"  - 審查判定 (accepted): {review.get('accepted')}")
        
    print("=" * 75)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.abspath(os.path.join(current_dir, "..", "examples", "synthetic_terrain.vizasset"))
    inspect_renderer_skin_asset(sample_path)
