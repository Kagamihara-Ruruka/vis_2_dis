# RendererSkinAsset 契約規格書 (RFC 草案 v0.2.1)

* **狀態**：Draft RFC (待 Owner 審閱，**尚未授權產品 Repo 實作**)
* **定位**：高品質 RFC 草案（非最終生產規格 v1.0.0），旨在作為「壓縮層（`rrkal-visual-compressor`）」與「渲染層（`RRKAL_displaytools`）」物理對接時的跨 Agent 協同討論基準（RFC 靈感來源）。
* **核心哲學**：
  1. **零程式碼耦合**：拒絕直接 `import` 產生的依賴螺旋。透過結構化聲明與標準 Payload 對接。
  2. **資產相容性**：不顛覆現行 `.vizasset` 生態，將皮層（Skin Asset）作為 `.vizasset` 的混合封裝與 Payload 擴充。
  3. **實用主義至上**：第一階段不強制推行 CDF 5/3 小波二進位極限壓縮，而以量化（Quantization）、多級金字塔（LOD Pyramid）與瓦片快取（Tile Cache）作為基準實作，確保系統之高強健性與可還原性。

---

## A. Non-goals (非本階段目標)

* 不取代 `.vizasset` 作為 RRKAL 編輯器首選的穩定手動容器。
* 不定義專有的底層二進位封裝格式，第一版僅採用通用且廣受支持的 NumPy 壓縮封裝。
* 不要求渲染器直接讀取未經清洗或量化的原始數據源。
* v0 階段不要求實作 CDF 5/3 或 Haar 小波二進位極限壓縮，亦不承諾 native GPU 實時小波重構。
* v0 階段不要求支援動態 runtime 瓦片切片流式傳輸（Tile Streaming）。

---

## B. Relationship with .vizasset (與既有資產的關係)

`RendererSkinAsset` 並非用以取代 `.vizasset`，而是其內部組織形式 of Payload 約定或可被外部 Registry 說明的 skin package。我們支援兩種物理封裝模式：

### 模式 A：嵌入式皮層 (Embedded Skin) — 【v0 優先推行模式】
皮層結構作為 `.vizasset` 容器內部的一個特定目錄結構，與 Provenance 檔案共存：
```text
terrain_gebco_2025.vizasset/
├── asset.json                   # 整體容器聲明 (Provenance)
├── metrics.json                 # 整體資產評測指標
├── review.json                  # 整體 Review Packet 驗證證據
├── preview.svg                  # 快速預覽
├── skins/                       # 存放針對各渲染層最佳化的皮層
│   └── terrain/
│       ├── manifest.json        # 皮層專屬 manifest
│       └── payloads/            # 數值高度與覆蓋率資料
│           ├── elevation_l0_i16.npz
│           ├── elevation_l1_i16.npz
│           └── coverage/
└── demo.py                      # 自我驗證展示碼
```

### 模式 B：獨立式皮層 (Standalone Skin) — 【未來可選模式】
皮層獨立以 `.skin/` 目錄存在，但必須在其 `asset.json` 中明確說明其關聯的 `.vizasset` 或被 RRKAL Registry 進行全局 Reference 指向。

---

## F. Owner Approval Policy (Owner 審批政策)

* **審批紅線**：**本 RFC 在獲得 Owner 明確書面或指令批准前，絕對不得被實裝至任何產品代碼主線。**
* **授權範圍**：Owner 已正式授權外部原型（External Reference Prototype）工作，允許在 `./vis_2_dis/` 與 `./AGENT_EXCHANGE/` 目錄中進行建置與程式碼實裝。
* **唯讀紅線**：三個主要產品 Repo (`APIkeys_collection`、`rrkal-visual-compressor`、`RRKAL_displaytools`) 均維持唯讀。除非 Owner 另行給出明確的產品實作授權，否則主寫同伴 `c_2` 與 `c_3` 僅可針對接口、欄位 Schema、可行性與風險提出文字性審查與修改建議（Review-only），不可進入 Repo 開發。

---

## 1. RendererSkinAsset 物理結構與檔案大小校驗

在 `manifest.json` 中，我們對每一個 LOD 等級的實體檔案大小進行了嚴格的雙重定義，以防止在驗證時因壓縮比率或格式頭開銷產生判斷失準：

* `"raw_nbytes"`：指矩陣完全載入內存後的原始未壓縮二進位位元組大小（例如：$2160 \times 4320 \times 2\ \text{bytes} = 18,662,400\ \text{bytes}$）。
* `"file_size_bytes"`：指該級實體 `.npz` 壓縮檔在磁碟上的真實檔案大小，供驗證器直接比對。
* `"compression"`：指定壓縮算法，預設為 `"npz_deflate"`。

---

## 2. manifest.json Schema 設計 (v0.2.1)

```json
{
  "schema": "rrkal.renderer_skin_asset.v0.2.1",
  "kind": "terrain",
  "asset_id": "terrain_gebco_2025_v0.2.1",
  "source_dataset": "GEBCO_2025_Grid",
  "source_fingerprint": "sha256:<64 lowercase hex chars>",
  "encoding": {
    "type": "int16_meter",
    "scale": 0.5,
    "offset": 0.0,
    "nodata_value": -32768
  },
  "projection": {
    "system": "EPSG:4326",
    "datum": "WGS84",
    "unit": "degree"
  },
  "grid": {
    "row_order": "south_to_north",
    "col_order": "west_to_east",
    "bounds_semantics": "grid_points_inclusive",
    "lon_wrap": "[-180,180]",
    "lat_index_formula": "row = (lat + 90) / 180 * (height - 1)",
    "lon_index_formula": "col = (lon + 180) / 360 * (width - 1)"
  },
  "bounds": {
    "lat_min": -90.0,
    "lat_max": 90.0,
    "lon_min": -180.0,
    "lon_max": 180.0
  },
  "limits": {
    "max_dimension": 65536,
    "max_levels": 12,
    "max_payload_bytes": 1073741824,
    "allow_pickle": false
  },
  "levels": [
    {
      "level": 0,
      "path": "payloads/elevation_l0_i16.npz",
      "shape": [2160, 4320],
      "cell_size_deg": 0.08333333,
      "raw_nbytes": 18662400,
      "file_size_bytes": 12456789,
      "compression": "npz_deflate",
      "valid_mask": "payloads/coverage/valid_elevation_mask_l0_u8.npz",
      "land_fraction": "payloads/coverage/land_fraction_l0_u8.npz",
      "water_fraction": "payloads/coverage/water_fraction_l0_u8.npz"
    },
    {
      "level": 1,
      "path": "payloads/elevation_l1_i16.npz",
      "shape": [1080, 2160],
      "cell_size_deg": 0.16666666,
      "raw_nbytes": 4665600,
      "file_size_bytes": 3123456,
      "compression": "npz_deflate",
      "valid_mask": "payloads/coverage/valid_elevation_mask_l1_u8.npz",
      "land_fraction": "payloads/coverage/land_fraction_l1_u8.npz",
      "water_fraction": "payloads/coverage/water_fraction_l1_u8.npz"
    }
  ],
  "checksums": {
    "payloads/elevation_l0_i16.npz": "sha256:<64 lowercase hex chars>",
    "payloads/elevation_l1_i16.npz": "sha256:<64 lowercase hex chars>",
    "payloads/coverage/land_fraction_l0_u8.npz": "sha256:<64 lowercase hex chars>",
    "payloads/coverage/land_fraction_l1_u8.npz": "sha256:<64 lowercase hex chars>",
    "payloads/coverage/water_fraction_l0_u8.npz": "sha256:<64 lowercase hex chars>",
    "payloads/coverage/water_fraction_l1_u8.npz": "sha256:<64 lowercase hex chars>",
    "payloads/coverage/valid_elevation_mask_l0_u8.npz": "sha256:<64 lowercase hex chars>",
    "payloads/coverage/valid_elevation_mask_l1_u8.npz": "sha256:<64 lowercase hex chars>"
  },
  "status": "ready"
}
```

---

## 3. Data-to-Skin Interface 規範 (資料層 -> 皮層資產)

該接口負責將高精度的地形/海床高程原始數據轉換為適合渲染端低負載讀取的皮層資產。

### 3.1 量化與編碼策略 (Quantization)
* **量化公式**：
  $$val_{int16} = \text{clamp}\left(\left\lfloor \frac{val_{float} - \text{offset}}{\text{scale}} + 0.5 \right\rfloor, -32767, 32767\right)$$
  若為無效值 (NoData)，則強制設為 `nodata_value`（如 `-32768`）。
* **Scale 決定機制**：地形高度以 `0.5m` 或 `1.0m` 為量化步長（`scale=0.5`）。

### 3.2 LOD 多級金字塔下採樣策略
* **禁止 Nearest Neighbor 作為唯一正式的 LOD 生成策略**，以防低解析度下產生嚴重的走樣（Aliasing）。
* **地形高度 (Elevation)**：第一版（v0）必須支援 **區塊平均 (Block Average) / 最小與最大值 (Min/Max Summary)** 下採樣；中位數 (Median) 下採樣設為可選 (Optional)；亦可選支援更高級的高斯 (Gaussian) 或 Lanczos-3 下採樣。
* **陸水覆蓋率 (Coverage)**：採用面積佔比（Area Fraction）計算。
* **二值遮罩 (Mask)**：採用多數決（Majority）或特定比例判定。
* 每一級 LOD 的高度圖皆必須有對應等級的 `land_fraction` 與 `water_fraction`，以確保各層級之間不會因解析度不對齊產生格子縫隙。

### 3.3 緯度相關 LOD 解析度考量 (Latitude-Aware LOD)
在全域的 EPSG:4326 投影中，`cell_size_deg`（如 `0.083333`）僅作為網格邊界定義，其代表的實際物理公里數會隨著緯度變動（計算公式：$\text{lon\_km\_per\_degree} = \cos(\text{lat}) \times 111\ \text{km}$）。
* **渲染器決策註記**：渲染器在利用 `km_per_pixel` 進行 LOD 選擇時，必須在計算中引入緯度權重，以防止在高緯度地區產生過度採樣（Over-sampling）或欠採樣（Under-sampling）。

### 3.4 物理指標計算與 Review Packet 封裝
* **保真度評估**：對比原始數據與重構還原後的浮點數據，計算高度的 **RMSE (均方根誤差)**、**MAE (平均絕對誤差)**、**P95 絕對誤差**、**Max Error (最大絕對誤差)**。
* **SSIM (結構相似性)** 僅作為可選指標，因其對純物理地形數據的拓撲幾何保真度衡量不如 MAE 與 RMSE 直接精準。
* 將所有的評測數據與來源指紋 (`source_fingerprint`) 合併包裝寫入 `review.json`。

---

## 4. Skin-to-Renderer Interface 規範 (皮層資產 -> 渲染層)

渲染層調用此接口，以安全且極速的手段加載皮層資產。

### 4.1 載入端安全校驗與 Ingestion 防線
由於 Payload 封裝採用 NumPy 的 `.npz` 格式，渲染器載入時必須嚴格執行防禦型編程，堅決防範 **Memory Bomb**。實務 Ingestion 加載檢查流程如下：
1. **實體大小驗證**：加載前，先比對實體檔案大小是否與 `manifest.json` 中宣告 wholesalers 的 `file_size_bytes` 完全一致，防範截斷或不完整寫入。
2. **路徑安全校驗 (Path Traversal Protection)**：校驗加載的 path 必須完全位於資產 root 目錄樹之內，杜絕利用相對路徑 `../` 進行目錄遍歷攻擊。
3. **反序列化防禦**：必須強制調用 `np.load(path, allow_pickle=False)`，禁止載入包含任意 Python 物件的反序列化後門，防範惡意代碼注入。
4. **提前限制與陣列鍵校驗**：
   - 限制 `.npz` 中的陣列數量及解開後的鍵值 (Keys) 數量不得超過規格預期。
   - 校驗 `.npz` 中的鍵值名稱必須僅包含在預設的允許集合中（如地形高程僅允許 `data`、`min`、`max` 等），防止記憶體溢出。
5. **類型與維度二次校驗 (不信任內部屬性)**：
   - 載入 data array 後，不得信任其內部的維度屬性。必須再次與 manifest 中宣告的 `dtype`、`ndim`、`shape` 以及物理 `nbytes` 進行嚴格比對。
6. **硬性限制過濾**：
   - 地理維度大小不得超過 `limits.max_dimension`（如 65536）。
   - LOD 級數不得超過 `limits.max_levels`（如 12 級）。
   - 單一 Payload 二進位大小不得超過 `limits.max_payload_bytes`（如 1GB）。

### 4.2 渲染採樣策略 (Renderer Sampling Policy)
* **連續型純物理場 (Continuous Scalar Field)**：如海面高度（Elevation）、海面溫度（SST）、葉綠素濃度（CHL）、濁度（Kd490），**預設採用雙線性插值 (Bilinear Sampling)**，以獲得平滑的坡度與視覺轉折。
* **類別與二值遮罩 (Categorical Mask / Discrete Class)**：如 `valid_mask`、陸海邊界類別，**預設採用 Nearest Neighbor 採樣**，確保特徵邊界尖銳且無中間過渡模糊值。
* **覆蓋率佔比 (Coverage Fraction)**：如水陸 fraction，可支援 Bilinear 插值渲染。

### 4.3 邊界填充與縫合 (Boundary Stitching)
* 為了消滅多個相鄰皮層瓦片在雙線性插值採樣時產生的 1-pixel 寬度缝隙，v0 皮層在生成時可選擇在瓦片周圍多生成 1 圈邊界 Padding 像素。若無 Padding，則渲染器需強制採用 `CLAMP_TO_EDGE` 或是實施 Index Stitching 拓撲縫合。

---

## 5. TerrainSkinAsset v0.2.1 具體規格定義

* **高程 Payload (`elevation_lX_i16.npz`)**：內含一個 `"data"` 鍵的 2D `int16` 矩陣。
* **高程有效性覆蓋率 (`elevation coverage`)**：**必須採用對應 LOD 層級下的 `valid_mask` 遮罩**作為判定地形是否存在的唯一依據。
* **陸水混色特徵 (`land_fraction` / `water_fraction`)**：僅作為地表材質混合（Surface Material Blending）與著色器分類輸入，**不代表地形的物理存在覆蓋率**。
* **MinMax 金字塔 (`minmax_lX_i16.npz`)**：
  * **定位**：作為未來 Tile Culling、Horizon Culling、LOD 選擇以及 normal/slope 坡度估計的輔助參考資料。**v0 階段不承諾藉此完成完整的 Frustum Culling**。

---

## 6. OceanOpticsSkinAsset v0.2.1 具體規格定義

海洋光學主要關注連續濁度與多光譜漫射。

* **$K_d(490)$ 濁度金字塔與 Log Scale 精度**：
  * 由於漫射衰減係數呈現高度非線性特徵，必須採用 Log-scale 進行量化儲存，且下界不得為 0.0。
  * 規格定義如下：
    ```json
    {
      "layer_id": "kd490",
      "unit": "m^-1",
      "scale": "log",
      "valid_range": [0.01, 2.0],
      "clamp_range": [0.001, 10.0],
      "log_epsilon": 0.001
    }
    ```
  * 將 10.0 作為極限截斷上限 (`clamp_range`)，而將 `0.01 ~ 2.0` 作為預設的視覺有效範圍 (`valid_range`)。

---

## 7. RenderLayerSpec 渲染圖層規範 (v0.2.1)

```json
{
  "schema": "rrkal_displaytools.render_layer_spec.v0.2.1",
  "layer_id": "gebco_terrain_layer",
  "layer_type": "terrain_skin",
  "source_skin_asset": "terrain_gebco_2025_v0.2.1",
  "source_manifest": "skins/terrain/manifest.json",
  "visible": true,
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
    "resolve_by_lod": true,
    "opaque_mask": {
      "opaque_mask_kind": "terrain_opaque_mask",
      "threshold": 255
    },
    "requires_underlay": false
  },
  "update_policy": {
    "interactive": "cached",
    "settled": "refresh_if_dirty",
    "export": "require_ready"
  },
  "status": "ready"
}
```

---

## 8. 圖層遮蔽與算力省除優化 (Composition Optimization)

為了最大程度地節省 GPU 渲染與採樣算力，渲染引擎實施以下優化規則：

* **當前影格完全遮蔽 (Per-Frame Occlusion Jump)**：
  * **優化 Hint**：完全遮蔽跳過為渲染器的優化提示（Optimization Hint）。渲染器在 v0 階段可以安全忽略它。
  * **影格級跳過**：若實施該優化，當上層圖層在當前繪製影格的特定像素或瓦片區域（Tile / Pixel Region）滿足 `opacity == 1.0`、`blend_mode == "normal"` 且 `opaque_mask` 數值達到或大於門檻值時，**則該區域下方所有圖層可直接跳過當前影格 (Per-Frame) 的 Sampling、Shading 與 Composition 計算**，省除 GPU 負荷。
* **生命週期保護 (Life-Cycle Isolation)**：
  * **安全紅線**：遮蔽優化**僅適用於當前影格的 GPU 繪製成本省除，絕對不得因此跳過資產生命週期中的 Ingestion、Checksum Validation、Cache Registration 或 Background Preparation**，保障系統全局狀態的一致性。

---

## C. Failure Behavior (錯誤處理與降級行為)

在加載與解析過程中，渲染器需遵循以下降級策略：
* **缺失 Payload (Missing Payload)**：將該圖層狀態設置為 `failed`，畫面降級至底圖，不引發主進程崩潰。
* **指紋不匹配 (Checksum Mismatch)**：立即拒絕載入該資產（Reject Asset），防範損壞或篡改文件。
* **未知編碼格式 (Unsupported Encoding)**：設置狀態為 `review_required` 並拋出警告。
* **層級丟失 (Level Missing)**：在 Manifest 允許範圍內，自動尋找最近的可用低解析度層級進行插值 fallback 渲染。
* **缺失遮罩 (Valid Mask Missing)**：僅在 Manifest 明確允許時，方可默認全區域有效，否則需拋出異常。

---

## D. Runtime Mode (執行期模式)

皮層加載與更新需與 Displaytools 的主渲染優化線高度契合，分為四種運行模式：
1. **Interactive (交互模式)**：採用較低解析度 LOD（如 level 2），使用快取數據，**以此作為降低 frame cost 並向 60 FPS 推進的互動目標**（實際幀率需由 runtime profiler 進行真實驗證，不作硬性承諾）。
2. **Preview (預覽模式)**：採用 level 1 解析度，執行異步漸進式刷新。
3. **Quality (高品質模式)**：載入 level 0 原始解壓精度，開啟完整雙線性插值與光影計算。
4. **Export (匯出模式)**：強制要求所有 LOD 數據載入就緒 (`require_ready`)，進行精確的高畫質靜態渲染匯出。

---

## E. Implementation Staging (分步實作進程)

本規格書的落地建議分為以下六個階段逐步實施：
* **Stage 0**：RFC 討論、評審與修訂（【當前所處階段】）。
* **Stage 1**：TerrainSkinAsset 合成生成器（Synthetic Builder）PoC，用以生成虛擬的高度金字塔 NPZ 檔案。
* **Stage 2**：Skin-to-Renderer 預覽載入器實裝，驗證安全 NPZ 防禦性 Ingestion。
* **Stage 3**：OceanOpticsSkinAsset 濁度與 Log Scale 量化生成與驗證。
* **Stage 4**：真實地形與海床數據源對接（例如 GEBCO_2025 或 ETOPO 格網），進行正式轉化。
* **Stage 5**（未來擴充）：小波變換二進位 Codec 插件（`.vizc`）集成。

---
*起草單位：Antigravity AI 架構師*  
*審閱狀態：**待 Owner 審閱；尚未授權產品 Repo 實作。** (Review Status: Pending Owner Review. Implementation approval: Not granted. External prototype authorized.)*
