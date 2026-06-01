#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspect_renderer_skin_asset.py
功能：對 TerrainSkinAsset 進行 CLI 可讀化診斷與結構性檢查。
說明：
1. 檢查並顯示 source_fingerprint 的合法性。
2. 對金字塔每一級的 elevation, valid_mask, land_fraction, water_fraction, minmax 進行實體 Checksum 校驗。
3. 計算並顯示 LOD 壓縮比 (Compression Ratio = raw_nbytes / file_size_bytes)。
4. 顯示 coverage payload 完整度與 review.json 的真實高程誤差 (RMSE, MAE, p95)。
"""

import os
import json
import hashlib
import re

def calculate_sha256(filepath):
    """計算檔案的 SHA-256 哈希值"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"

def inspect_renderer_skin_asset(asset_dir):
    """診斷皮層資產內容"""
    print("=" * 70)
    print(f"  [TerrainSkinAsset CLI 診斷工具] - {os.path.basename(asset_dir)}")
    print("=" * 70)
    
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
    
    print("-" * 60)
    print("  [皮層 Manifest 參數]")
    print("-" * 60)
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
        shape = lvl.get("shape")
        raw_nbytes = lvl.get("raw_nbytes")
        file_size = lvl.get("file_size_bytes")
        
        # 計算壓縮比 (raw_nbytes / file_size_bytes)
        comp_ratio = raw_nbytes / file_size if file_size > 0 else 0
        
        print(f"      [LOD {lvl_num}] shape={shape} | 內存={raw_nbytes}B | 實體={file_size}B | 壓縮比={comp_ratio:.2f}x")
        
        # 校驗各 Payload 實體檔案與 Checksum
        payloads = {
            "elevation": lvl.get("path"),
            "valid_mask": lvl.get("valid_mask"),
            "land_fraction": lvl.get("land_fraction"),
            "water_fraction": lvl.get("water_fraction"),
            "minmax": f"payloads/minmax_l{lvl_num}_i16.npz"
        }
        
        for name, rel_p in payloads.items():
            abs_p = os.path.join(skin_root, rel_p)
            if not os.path.exists(abs_p):
                print(f"        [-] {name:<15}: 🛑 檔案缺失 ({rel_p})")
                continue
                
            # Checksum 校驗
            declared_hash = checksums.get(rel_p)
            actual_hash = calculate_sha256(abs_p)
            if actual_hash == declared_hash:
                print(f"        [+] {name:<15}: ✅ Checksum 吻合 (PASS)")
            else:
                print(f"        [-] {name:<15}: 🛑 Checksum 損壞 (EXPECTED {declared_hash} | GOT {actual_hash})")
        
    # 讀取 review.json
    review_path = os.path.join(asset_dir, "review.json")
    if os.path.exists(review_path):
        with open(review_path, "r", encoding="utf-8") as f:
            review = json.load(f)
        print("-" * 60)
        print("  [Review Packet 實體量化誤差憑證]")
        print("-" * 60)
        fidelity = review.get("source_fidelity", {})
        print(f"  - 均方根高程誤差 (RMSE): {fidelity.get('rmse_meters'):.6f} 米")
        print(f"  - 平均絕對誤差 (MAE): {fidelity.get('mae_meters'):.6f} 米")
        print(f"  - P95 最大高程誤差: {fidelity.get('p95_absolute_error_meters'):.6f} 米")
        print(f"  - 最大量化絕對誤差 (Max): {fidelity.get('max_absolute_error_meters'):.6f} 米")
        print(f"  - 審查判定 (accepted): {review.get('accepted')}")
        
    print("=" * 70)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.abspath(os.path.join(current_dir, "..", "examples", "synthetic_terrain.vizasset"))
    inspect_renderer_skin_asset(sample_path)
