---
title: 離線 build → 靜態 JSON → 前端純讀 pattern
version: v1
last-updated: 2026-11-04
source: incentive_control_center / rs_sales_intelligence_center（去識別化）
---

# 離線 build → 靜態 JSON → 前端純讀 pattern

> BI dashboard 不用做成「打 DB 即時算」。對很多場景（200-300 concurrent、掛分頁不關、算法多樣），**離線 build → 靜態 JSON → 前端純讀** 是更划算、更凍結、更好 debug 的架構。這份文件說明何時用、怎麼設計。

## 情境（什麼時候拿出來用）

- BI 內部 dashboard，使用者數幾十到幾百
- 資料更新頻率 ≤ 每日幾次（不是每秒）
- 算法多樣、常改、需要版本化
- 使用者會「掛分頁不關」整天
- 不要花錢養一個 server-side 計算環境

## 核心主張

**打破直覺**：dashboard 不一定要「使用者打開 → server 查 DB → 回傳」。改成：

```
Day 1 02:00  排程 build → 寫靜態 JSON → 上 CDN／GCS
全天         使用者打開 → 前端讀 JSON → 純渲染（不算分）
```

**三大好處**：
- **成本幾乎零**：只付 CDN／GCS 存取費
- **凍結性好**：JSON 版本化 → 看歷史、回滾都可
- **算法可演化**：改算法重 build，前端不動

**代價**：
- 資料不即時（延遲 = 排程頻率）
- 不適合「使用者下指令、系統 recompute」類 app

---

## 架構圖

```
排程（cron / Windows 工作排程）
    │
    ▼
Pipeline：
  [source DB / Tableau CSV]
    │  讀取
    ▼
  compute.py（算分 + 組 JSON shape）
    │
    ▼
  output：data-<activity>.json + manifest.json
    │  上傳
    ▼
  GCS / S3 / CDN（靜態 bucket）
    │
    ▼  使用者打開
  Cloud Run / 靜態站 + IAP（身份驗證、不算分）
    │  lazy sync + 節流
    ▼
  User Browser
    │  fetch JSON、純渲染
```

**鐵則**：
- **Server-side 不算分**，只做 panel/track 級權限過濾
- 前端**純讀 JSON、純渲染**，不算分
- 每個資料集帶一個 manifest.json（含 generated_at、版本資訊）

---

## 設計要點

### 1. 分層：IO / Compute / 前端

```
IO 層     → read_data.py        從 source 讀，normalize, validate
Compute   → compute.py          算分 + 聚合 + 組 JSON shape（不碰 HTML）
Build     → build.py            compute() + 蓋 generated_at → 寫 web/data.json
前端      → web/*.mjs           fetch data.json，純渲染
```

**鐵則**：
- **單向 import**：read_data → compute（compute 不反向）
- Compute **只吐 dict**（不碰 HTML、不碰檔案 I/O）
- 前端吃 JSON **shape 契約**（見下）

### 2. JSON shape 契約

前後端的契約檔（`data-contract.md`）：

```json
{
  "generated_at": "2026-11-04T02:00:00Z",
  "spec_version": "v1.2",
  "tracks": {
    "track_id_A": {
      "modules": [
        { "type": "...", "data": [...] },
        ...
      ]
    },
    "track_id_B": {
      ...
    }
  }
}
```

**契約鐵則**：
- 前端只依契約的 shape 渲染，不假設其他欄位
- 改 shape = 改契約 = 改前後端
- 新增欄位 = 版本號 bump
- 刪欄位 = 前端要先改相容

### 3. 權限過濾放在哪

**三種做法**：

| 做法 | 優 | 劣 | 適用 |
|------|---|---|------|
| A. Build 階段分多個 JSON（每群組一份） | 前端最單純 | 群組多時檔案爆 | 群組 ≤ 10 |
| B. 一份 JSON + 前端 filter | 檔案單一 | 資料暴露給客戶端 | 無敏感資料 |
| C. 中間 Cloud Run 做 panel filter | 平衡 | 多一層 | 預設 |

**預設 C**：Cloud Run **只做權限過濾**，不算分。

### 4. 資料契約檔（給人／AI 看）

每個資料集帶一份 `sample-13m.csv`（committed）：
- 用途：schema snapshot，給人與 AI agent 看欄位長相
- **不被 pipeline 消費**，純當參考檔
- 真實資料由 pipeline 動態拉（gitignored）

**好處**：
- 新人／AI 不用翻 DB 就知道欄位
- 版控追蹤 schema 變動
- 離線也能理解資料結構

### 5. 每日 pipeline 編排

```python
# python -m pipeline
# 一條龍：extract → build → push

def main():
    1. 拉 13m.csv（從 Tableau Prep / source）
    2. 掃 activity/*/app/compute.py，動態 import 呼叫 main()
    3. 寫 web/data-*.json + manifest.json
    4. push 到 GCS
```

**原則**：
- 一條指令跑完一條龍
- 單個活動失敗不擋其他活動（錯誤隔離）
- 最後上傳的是 manifest.json（保證原子性）
- 整條 run time 目標 < 1 分鐘

---

## 何時不要用這 pattern

- **使用者下指令要即時 recompute**（例：ad-hoc query tool）
- **資料秒級新**（例：交易監控）
- **100% 使用者各看不同切面**（分片 JSON 爆炸）
- **使用者數上千 + concurrent 高**（CDN 流量成本開始超越 server）

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| Server-side 偷算 | 架構失去凍結性、成本升 | 強制：server 只過濾、不算 |
| 前端吃直接 DB | 違背 pattern | JSON 是唯一真實 |
| JSON shape 改了前端不知 | 渲染壞 | 契約檔版本化 |
| 不寫 manifest | 不知道 JSON 新不新 | manifest 含 generated_at |
| 權限在前端做 | 資料暴露 | 權限在 Cloud Run 做 |
| pipeline 一個活動失敗全掛 | 錯誤傳播 | 每活動獨立 try/except |
| 直接推 data.json 不推 manifest | 讀者可能讀到 partial | 最後才推 manifest |
| 讓 compute 回傳 HTML | 違背單一職責 | compute 只回 dict |
| 範本資料被 pipeline 消費 | 真實資料被覆蓋 | sample 檔明文「不被 pipeline 吃」 |

---

## 檢核清單

- [ ] Server-side 不算分、只過濾？
- [ ] 前端吃 JSON 不打 DB？
- [ ] 分層單向 import（read_data → compute → build）？
- [ ] JSON shape 契約檔有嗎？
- [ ] 契約檔有版本號？
- [ ] Sample schema 檔 committed、不被 pipeline 消費？
- [ ] manifest.json 含 generated_at？
- [ ] 一條 pipeline 指令跑完？
- [ ] 錯誤隔離（單活動失敗不擋其他）？
- [ ] 權限過濾放對層（Cloud Run 不是前端）？

---

## 相關

- [[activity-folder-self-contained-pattern]] — 每個活動自成一夾，是這個 pattern 的組織方式
- [[data-flow-playbook-skeleton]] — 若要 scale 成 BI 團隊 SSOT，配這份用
- [[bi-knowledge-base-structure]] — 知識庫結構搭 IAP + GCS 架構相同

## 真實案例骨架（去識別化）

### 案例 1：200-300 concurrent，靜態站比動態便宜 10 倍
原本考慮 server-side 計算，估算要養 2-3 台 server + DB 連線池。
改成離線 build → GCS → 前端純讀後，每月成本從 N 千降到 N 百。使用者數增長到 500 時仍穩。

### 案例 2：算法改一次，前端完全不動
Compute 內改計分公式。重 build、推 GCS。前端下一次 fetch 自動拿到新結果。
**原因**：前端只吃 JSON shape，shape 沒變就不用動。

### 案例 3：JSON 版本化讓歷史回滾可行
某次改算法不如預期，業務要回昨天的版本。做法：GCS 檔有版本歷史、把前一版 copy 回來。1 分鐘回滾完。
動態 server 要回滾要 revert code + redeploy，10 倍時間。

### 案例 4：Sample 被 pipeline 吃掉
原本 `sample-13m.csv` 跟真實 `13m.csv` 同一個路徑，導致 pipeline 無資料時用了 sample 跑，產出 demo 數字當真實資料。
**校正**：sample 明文放別處，compute 從 `data/13m.csv` 讀、缺檔直接 raise、無 fallback。
