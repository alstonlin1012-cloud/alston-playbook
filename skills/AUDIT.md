---
title: Skill 去識別化審查報告
date: 2026-11-03
scope: 3 個候選 skill 的去識別化／可攜性檢查
---

# Skill 去識別化審查報告

## 總結

| Skill | 洩漏狀態 | 可攜性 | 動作 |
|-------|---------|--------|------|
| `validating-replacement-data-sources` | ✅ 無洩漏 | 可直接帶 | **已複製** |
| `decomposing-market-decline` | ✅ 無洩漏 | 可直接帶 | **已複製** |
| `store-handover-impact` | ⚠️ 保留門市／品牌／加盟商名（使用者授權，門市已關） | 可帶（已剝離內部連結） | **已複製**，見下方說明 |

---

## Skill 1：`validating-replacement-data-sources` ✅

**掃描**：grep `Gogoro|GoShare|SYM|KYMCO|YAMAHA|BQ schema|GGR_AI|具體地名`，**零命中**。
**判斷**：skill 本身就寫得通用（新舊資料源遷移驗證），沒嵌入公司特定內容。
**動作**：**已原封複製**到 `alston-playbook/skills/`。
**可補強**：加一個產業範例段落（例：資料倉儲遷移、CRM 換系統）讓它更有肉。

---

## Skill 2：`decomposing-market-decline` ✅

**掃描**：零命中。
**判斷**：純方法論（市場衰退的「母體 vs 行為」二層拆解），本就產業中性。
**動作**：**已原封複製**。
**可補強**：加決策樹圖、加 2-3 個虛構案例（不限產業）。

---

## Skill 3：`store-handover-impact` ⚠️ 使用者授權保留門市／品牌名

**2026-11-03 使用者授權**：門市已關、品牌／加盟商名可保留，影響可接受。

**動作已做**：
- 複製整個 skill 到 `alston-playbook/skills/store-handover-impact/`
- 剝離內部連結（`bap.gogoro.com/...` → `<internal-registration-workbook>`）
- 保留：真實門市名、品牌（GOGORO/KYMCO/SYM/YAMAHA/WEMO）、加盟商名（康寶動力／睿能／宏運／泰昇／合鑫）、具體數字、`case-real-yongkang/`、`domain-motorcycle.md`

**為什麼仍要注意**：
- 加盟商公司仍營運中，未來若有版本公開（開源／blog），需再做一次抽象
- 建議：本地／private git 使用時沿用現狀；若要公開分享前再做路線 B

---

### 原洩漏盤點（已不作為封鎖，僅存檔參考）

### 洩漏盤點

#### `README.md`（高）
- 真實門市名：`永康中華`、`安平中華`、`台南新營`
- 真實加盟商：`睿能`、`康寶動力`
- 內部連結與資料路徑：`tests/case-real-yongkang/`、`data/`（業務資料）
- 自己也承認：「含真實營運數據（門市名、市占率、業務人數、領牌量）。GitLab repo 必須設為 Private」

#### `references/domain-motorcycle.md`（最嚴重）
- 品牌：`GOGORO`、`WEMO`、`KYMCO`、`SYM`、`YAMAHA`
- 內部欄位：`GTM_KeyBrand`、`MVO_Area`、`tag_wemo`
- 內部檔名／schema：`tainan_reg_data.csv`、`行政區.csv`、`analysis_area_flow.py`
- 具體數字：`台南 GOGORO 2025H1 = 1,187 台、全台 = 11,830 台`、`永康區 KYMCO 1,130／SYM 1,858／SYM 1,991`
- 具體市占：`台南約佔全台 10%`
- 內部連結：`https://bap.gogoro.com/authoring/_17679519649180/13#2`
- 具體快照日：`2026-07-20 起該欄已整個移除`
- 具體區域／門市：`永康區`、`大內區`、`臺北市`、各地名

#### `references/judgment-framework.md`（中）
- `GOGORO` 字樣散落
- 具體場景：「該區 GOGORO 市占 4%→3.33%、同期競品接手 60 台」

#### `tests/`（嚴重）
- `case-real-yongkang/expected.md`：真實門市分析結果
- `make_fixtures*.py`：真實地名（台中中區、彰化、南投、桃園蘆竹、新竹、嘉義…）、GOGORO 字樣、具體加盟商（宏運、泰昇、合鑫）
- `case-cross-city/reg.csv` 等 fixture CSV：GOGORO、具體地名

#### `scripts/loader_template.py`
- 未檢，推測含欄位名假設

### 可攜但需大改——建議計畫

**切兩路**：

**路線 A — 快版（1-2 天）**：純判準框架帶走，domain 檔整個刪
- 保留：`SKILL.md`、`references/judgment-framework.md`（去 GOGORO 字樣）
- 刪除：`references/domain-motorcycle.md`（整份機車業 domain 等於洩漏地圖）
- 保留：`tests/` 的合成 fixtures（去真實地名、去 GOGORO 字樣）
- **刪除**：`tests/case-real-yongkang/`（含真實資料，法律風險最高）
- **成果**：「門市 handover 影響分析」通用判準框架，不綁產業

**路線 B — 完整版（1 週）**：抽象到「加盟型通路 handover」通用層
- 另寫 `references/domain-template.md`，說明如何為任何產業補 domain 檔
- `judgment-framework.md` 全面去品牌（`<Brand A>` 等）
- 新增 2 個虛構 domain 範例：零售連鎖、餐飲加盟
- tests 全部用虛構地名與公司
- **成果**：真正可販賣／可開源的 skill

### 推薦

**先走路線 A**，離職後有需要再升級成路線 B。路線 A 的具體步驟：

1. 複製 `store-handover-impact/` 整個到 `alston-playbook/skills/`
2. 跑一次「全檔替換」清單：
   ```
   GOGORO           → <Brand A>（自家品牌）
   WEMO             → <Shared-fleet brand>
   KYMCO/SYM/YAMAHA → <Brand B> / <Brand C> / <Brand D>
   睿能 / 康寶動力  → <Operator A> / <Operator B>
   宏運 / 泰昇 / 合鑫 → <Franchisee N>
   永康中華／安平中華／任何真實門市 → <Store #N>
   台南市／永康區／各實地名 → <City South> / <District #N>（或直接刪）
   tainan_reg_data  → <registration-dataset>
   行政區.csv       → <district-level.csv>
   MVO_Area         → <registration-area>
   GTM_KeyBrand     → <brand-key>
   tag_wemo         → <fleet-tag>
   bap.gogoro.com 連結 → 刪
   具體數字（1,187 台…）→ 區間或拿掉
   具體快照日       → 相對時間（T0+3M）
   ```
3. 刪除 `tests/case-real-yongkang/` 整個資料夾
4. 刪除 `references/domain-motorcycle.md` 檔案
5. 把判準框架抽象部分留下（判準邏輯本身是方法論，不洩漏）

### 法律警語

`store-handover-impact` 現狀是**公司資產**（含真實門市經營數據），**不可**：
- push 到個人 GitHub／GitLab
- 分享給外部任何人
- 複製到個人雲端未去識別化前

**只有判準框架的方法論部分**（怎麼寫判準、怎麼設 ✅/⚠️/❌/⬜ 判準、三視角檢查）是方法論，屬於個人 know-how 可帶。

---

## 下一步建議

1. 立刻可做：驗證 skill 2、3 在新環境可正常載入（`claude code` 下看能否 trigger）
2. 本週內：決定 skill 3 走路線 A 還是 B，動手做去識別化
3. 離職前最後一天：掃一次全 repo 確認沒有真實字串，用這個 grep：
   ```bash
   cd ~/Desktop/alston-playbook
   grep -rniE 'Gogoro|GoShare|SYM|KYMCO|YAMAHA|GGR_AI|gogoro-twbi|gsh_tw|睿能|康寶|宏運|泰昇|合鑫|永康|安平|海佃|仁武|岡山|bap\.gogoro' .
   ```
   期待 0 命中。
