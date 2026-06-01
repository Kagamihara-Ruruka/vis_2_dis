# PROJECT GTD - vis_2_dis 中介契約層項目管理

本文件追蹤 `vis_2_dis`（中介契約層外部原型）Staging 進度，用以引導跨 Agent 協同討論，並為未來的產品 Repo 對接做技術準備。

---

## 1. 核心 Staging 開發進程

- `[x]` **Stage 0: RFC 討論、評審與修訂**
    - 成功起草並發布 [renderer_skin_asset_rfc_v0.2.1.md](file:///Users/yen-an/Library/CloudStorage/CloudMounter-Google#2/vis_2_dis/specs/renderer_skin_asset_rfc_v0.2.1.md)。
    - 完成與 displaytools 連續場/Mask 採樣對齊，及 `south_to_north` 座標映射適配。
- `[x]` **Stage 1: TerrainSkinAsset 合成生成器與 Ingestion 驗證器實裝**
    - 實裝 `build_synthetic_terrain_skin.py`：支持 `int16` 高度量化與 Checksums 範例。
    - 實裝 `validate_renderer_skin_asset.py`：提供 Ingestion 安全 numpy allow_pickle 與 memory bomb 防禦。
    - 實裝 `build_render_layer_spec.py` 與 `inspect_renderer_skin_asset.py`。
    - 執行外部原型端到端自檢，全部防禦指標綠燈通過。
- `[x]` **Stage 2: 雙端主寫異步評審與設計意見收集**
    - 通過 `AGENT_EXCHANGE/inbox/` 發信提請 `c_2` 與 `c_3` 僅針對 RFC v0.2.1 及外部原型代碼進行文字評審。
- `[frozen]` **Stage 3: OceanOpticsSkinAsset 濁度與 Log Scale 量化生成與驗證 (已暫停/凍結)**
    - *說明：根據 Owner 2026-06-01 20:45 裁決，本專案工作已於 v0.2.2 基準線凍結。優先級正式回歸至 `RRKAL_displaytools` 渲染性能優化。*
- `[frozen]` **Stage 4: 真實地形與海床數據源對接 (GEBCO / ETOPO) (已暫停/凍結)**
- `[frozen]` **Stage 5: 小波變換二進位 Codec 插件 (.vizc) 集成 (已暫停/凍結)**

---

## 2. 項目開發守則 (唯讀邊界)

1. **產品代碼 100% 唯讀**：任何 Stage 均嚴禁主動修改 `APIkeys_collection`、`rrkal-visual-compressor`、`RRKAL_displaytools` 內部代碼。
2. **安全第一**：Ingestion 驗證器防線是渲染器防範 memory bomb 的第一防線，未來產品 Repo 實裝時必須無條件優先實作此驗證器。
