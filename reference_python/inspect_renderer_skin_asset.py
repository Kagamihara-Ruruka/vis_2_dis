#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspect_renderer_skin_asset.py
功能：對 TerrainSkinAsset 進行 CLI 可讀化診斷與結構性檢查。
說明：
1. 讀取 manifest 資訊並優雅排版列印。
2. 列印 review.json 內的物理保真度（RMSE, MAE）。
3. 用於驗證合成包的完整度。
"""

import os
import json

def inspect_renderer_skin_asset(asset_dir):
    """診斷皮層資產內容"""
    print("=" * 60)
    print(f"  [TerrainSkinAsset CLI 診斷工具] - {os.path.basename(asset_dir)}")
    print("=" * 60)
    
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
        
    print("-" * 50)
    print("  [皮層 Manifest 參數]")
    print("-" * 50)
    print(f"  - 綱要版本: {manifest.get('schema')}")
    print(f"  - 編碼格式: {manifest.get('encoding', {}).get('type')}")
    print(f"  - 量化步長: {manifest.get('encoding', {}).get('scale')} 米")
    print(f"  - 投影系統: {manifest.get('projection', {}).get('system')}")
    print(f"  - 行列排布 (row_order): {manifest.get('grid', {}).get('row_order')}")
    print(f"  - 行列公式: {manifest.get('grid', {}).get('lat_index_formula')}")
    print(f"  - 地理經緯邊界:")
    bounds = manifest.get("bounds", {})
    print(f"      緯度: {bounds.get('lat_min')} 至 {bounds.get('lat_max')}")
    print(f"      經度: {bounds.get('lon_min')} 至 {bounds.get('lon_max')}")
    
    print("\n  - 金字塔 LOD 層級列表:")
    for lvl in manifest.get("levels", []):
        print(f"      [LOD {lvl.get('level')}]")
        print(f"        檔案路徑: {lvl.get('path')}")
        print(f"        網格維度 (shape): {lvl.get('shape')}")
        print(f"        內存大小: {lvl.get('raw_nbytes')} 位元組")
        print(f"        實體檔案大小: {lvl.get('file_size_bytes')} 位元組")
        print(f"        有效遮罩 (valid_mask): {lvl.get('valid_mask')}")
        
    # 讀取 review.json
    review_path = os.path.join(asset_dir, "review.json")
    if os.path.exists(review_path):
        with open(review_path, "r", encoding="utf-8") as f:
            review = json.load(f)
        print("-" * 50)
        print("  [Review Packet 保真度憑證]")
        print("-" * 50)
        fidelity = review.get("source_fidelity", {})
        print(f"  - 均方根高程誤差 (RMSE): {fidelity.get('rmse_meters')} 米")
        print(f"  - 平均絕對誤差 (MAE): {fidelity.get('mae_meters')} 米")
        print(f"  - P95 最大高程誤差: {fidelity.get('p95_absolute_error_meters')} 米")
        print(f"  - 審查判定 (accepted): {review.get('accepted')}")
        
    print("=" * 60)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.abspath(os.path.join(current_dir, "..", "examples", "synthetic_terrain.vizasset"))
    inspect_renderer_skin_asset(sample_path)
