# vis_2_dis ── RRKAL 中介契約層外部參考原型

本專案為 **`vis_2_dis`**，是「壓縮層（`rrkal-visual-compressor`）」與「渲染層（`RRKAL_displaytools`）」物理對接時的外部參考原型（External Reference Prototype）。

本專案基於最新的 **`renderer_skin_asset_rfc_v0.2.1`** 技術綱要建置，旨在演示如何透過結構化資產 Manifest 與強健的安全防線，實現兩大專案之間的絕對零程式碼耦合。

---

## 1. 核心解耦架構 (三層二接口)

本專案完美展示了以下解耦拓撲結構：

```text
  [ 資料層 / Lakehouse ]
            │
            ▼ (Data-to-Skin Interface)
  [ 皮層資產 / RendererSkinAsset ]  <--- 本外部原型展示核心
            │
            ▼ (Skin-to-Renderer Interface)
  [ 渲染層 / Displaytools / Taichi ]
```

### 兩大核心接口規範
* **Data-to-Skin Interface**：規範原始高程數據的量化（int16 量化）、LOD 多級金字塔生成、以及 `review.json` 物理保真度憑證（Review Packet）的固化封裝。
* **Skin-to-Renderer Interface**：規範渲染器載入資產時的安全防禦（防範 NPZ 反序列化與 Memory Bomb）、經緯度座標映射（Grid Convention）與多圖層完全遮蔽（Occlusion Jump）優化 hint。

---

## 2. 目錄與腳本結構

```text
vis_2_dis/
├── specs/
│   └── renderer_skin_asset_rfc_v0.2.1.md  # 核心契約規格書
├── reference_python/
│   ├── build_synthetic_terrain_skin.py    # 合成高度金字塔生成器 (Data-to-Skin)
│   ├── validate_renderer_skin_asset.py    # 安全 Ingestion 驗證器 (Skin-to-Renderer)
│   ├── build_render_layer_spec.py          # 圖層渲染規格建置器
│   └── inspect_renderer_skin_asset.py      # CLI 結構與保真度診斷工具
├── examples/
│   └── synthetic_terrain.vizasset/         # 實體測試包 (排除實體 npz)
├── notes/
│   └── product_repo_readonly_integration_review.md # 唯讀產品整合備忘
├── PROJECT_GTD.md                          # 專案 Staging 進度管理
└── README.zh-TW.md                         # 本說明書
```

---

## 3. 工業級安全防禦設計 (NPZ Ingestion 安全防線)

為了防範 NumPy `.npz` 格式在加載時可能引發的反序列化漏洞與 Memory Bomb 攻擊，`validate_renderer_skin_asset.py` 嚴格實作了以下安全載入防禦流程：

1. **實體大小比對**：載入前比對實體檔案大小是否與 Manifest 宣告位元組完全一致，防止截斷或寫入未完成。
2. **路徑安全檢查 (Path Traversal)**：校驗加載路徑必須完全位於資產 root 目錄樹之內，防止相對路徑 `../` 目錄遍歷攻擊。
3. **反序列化防禦**：強制調用 `np.load(path, allow_pickle=False)`，關閉 Python pickle 任意代碼注入漏洞。
4. **提前限制與鍵值過濾**：限制 `.npz` 中的鍵數量，且鍵名稱必須僅在預期允許集合內。
5. **維度與內存二次比對**：載入資料陣列後，不信任其內部維度屬性。再次與 Manifest 宣告之 `dtype`、`ndim`、`shape` 以及內存 `nbytes` 進行比對，防範超大維度的 Memory Bomb 溢出。

---

## 4. 快速開始 (Quick Start)

### 步驟 1：建置合成高度金字塔資產包
執行生成器，將模擬無損的高度與 valid_mask、水陸遮罩寫入 `examples/` 目錄中：
```bash
python3 ./reference_python/build_synthetic_terrain_skin.py
```

### 步驟 2：執行安全 Ingestion 驗證
對生成的實體資產包執行嚴密的防禦型安全校驗，驗證指紋與 Limits 是否完全合規：
```bash
python3 ./reference_python/validate_renderer_skin_asset.py
```

---

## F. Owner Approval Policy (Owner 審批政策)

* **授權邊界**：本專案為**外部參考原型專案**，已獲得 Owner 授權在 `vis_2_dis/` 與 `AGENT_EXCHANGE/` 中進行代碼編寫與遠端 Git 推送。
* **產品唯讀紅線**：三大產品 Repo (`APIkeys_collection`、`rrkal-visual-compressor`、`RRKAL_displaytools`) 均維持 **100% 唯讀**。尚未獲得產品 Repo 實作授權，請勿擅自更改產品原始碼。

---
*起草單位：Antigravity AI 架構師*  
*審閱狀態：待 RRKAL Project Owner 審閱；尚未授權產品 Repo 實作。 (Review Status: Pending Owner Review. Product implementation not authorized.)*
