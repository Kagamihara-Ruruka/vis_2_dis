#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_render_layer_spec.py
功能：自動生成 RenderLayerSpec 屬性設定檔。
說明：
1. 移除硬編碼的 l0 覆蓋路徑。
2. 使用 "resolve_by_lod": true 來達到高度解耦。
3. 規範 composition 遮蔽優化的 threshold。
"""

import os
import json

def build_render_layer_spec(output_path):
    """建置圖層渲染規格 JSON"""
    print(f"[*] 開始建置 RenderLayerSpec 於: {output_path}")
    
    spec_data = {
        "schema": "rrkal_displaytools.render_layer_spec.v0.2.1",
        "layer_id": "synthetic_terrain_layer",
        "layer_type": "terrain_skin",
        "source_skin_asset": "terrain_synthetic_v0.2.1",
        "source_manifest": "skins/terrain/manifest.json",
        "visible": True,
        "opacity": 1.0,
        "blend_mode": "normal",
        "render_queue_group": "opaque_terrain",
        "lod_policy": {
            "mode": "auto",
            "interactive_level": 2,
            "preview_level": 1,
            "quality_level": 0,
            "export_level": 0
        },
        "coverage": {
            "coverage_mask_kind": "valid_elevation_mask",
            "resolve_by_lod": True,
            "opaque_mask": {
                "opaque_mask_kind": "terrain_opaque_mask",
                "threshold": 255
            },
            "requires_underlay": False
        },
        "update_policy": {
            "interactive": "cached",
            "settled": "refresh_if_dirty",
            "export": "require_ready"
        },
        "status": "ready"
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(spec_data, f, indent=2, ensure_ascii=False)
        
    print("[+] RenderLayerSpec 屬性生成完成！")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_json = os.path.abspath(os.path.join(current_dir, "..", "examples", "synthetic_terrain.vizasset", "render_layer_spec.json"))
    build_render_layer_spec(target_json)
