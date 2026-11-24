---
title: 輕量團隊 tracker — 小團隊用 Google Sheets + Apps Script 取代 JIRA
version: v1
last-updated: 2026-11-11
source: internal bi_team_tracker（去識別化）
---

# 輕量團隊 tracker 骨架

> 3-5 人團隊常掉進一個陷阱：用 JIRA 太重（設 workflow、權限、欄位的成本 > 效益）；用散落的 Slack 訊息 + 口頭同步太輕（週會前要重新翻一遍）。這份 template 走中間路線：**單一 Google Sheet + 每週 snapshot JSON + AI agent 讀寫**，取代 JIRA 但保有可量化分析。

## 情境（什麼時候拿出來用）

- 團隊 3-5 人，同時手上 15-30 案
- 用 JIRA 建 workflow / 權限 / 欄位的成本 > 效益
- 儀式感（sprint / velocity）對這規模是負擔
- 工程流程未複雜到需綁 branch / PR / ticket
- 要能給老闆看「團隊時間花哪、誰在卡、過載了沒」
- 希望 AI agent 能讀寫這份資料（週報、月報、團隊性格分析）

## 核心主張

**單一 Google Sheet 當單一真相源 + 每週 snapshot + AI 自動化**：

- 所有人只在 Google Sheets 上作業，掌握整個團隊動態
- 沒有第二個工具、沒有第二個介面、沒有第二次資料重填
- 個人視角、團隊視角、細節視角都收斂在同一份試算表
- 週會、月報、老闆需求盤點、團隊性格分析都由這份試算表衍生
- AI agent 從這份試算表讀寫，補完人工做不動的自動化

**為什麼 Google Sheets 而非 JIRA / Notion**：
- 所有人熟悉、共編零學習成本
- Apps Script 可觸發 snapshot、grep、自動統計
- AI agent（Claude / Gemini）用 Sheets MCP 直接讀寫
- 單一檔案、無跨系統同步問題

---

## 骨架（三 sheet + 一 output 資料夾）

```
<team>_tracker.gsheet
├── [keep] 總覽（儀表板）         ← 給人看：週會主畫面
├── [keep] 項目主表               ← 給人寫：單一真相源、一列一案
├── [keep] 更新日誌               ← 給人記：逐筆事件流（供 AI 生報告用）
├── [external] 個人視圖           ← 用 Google Sheets Filter View 建，每人一個
└── [deferred] 週會紀錄 panel     ← Phase 3 用 Apps Script + JSON snapshot 啟用

output/   ← AI agent 產，非試算表
├── snapshots/        YYYY-Www_<timestamp>.json   每週 snapshot（diff 用）
├── weekly_reports/   YYYY-Www.md                 AI 生週報
└── monthly_reports/  YYYY-MM.md                  AI 生月報 + 團隊性格
```

**三張 sheet 的分工邏輯**：
- 「總覽」給人看（週會主畫面）
- 「項目主表」給人寫（單一真相源）
- 「更新日誌」給人記（事件流，供 AI 生報告用）

---

## 主表欄位設計（19 欄 v4）

| 欄 | 欄名 | 說明 |
|----|------|------|
| A | 案名 | **unique key**，snapshot diff 以它為準 |
| B | 類型 | 年度計畫 / 產品開發 / 主題分析 / 基礎建設 / 無情作業 |
| C | 屬性 | 老闆 A / 老闆 B / 業務部 / 自主 / ... 標「誰丟出來的」 |
| D | 分類 | 急 / 常規 / 改善 / 探索 ... |
| E | 負責人 | 單一負責人（不用「大家」） |
| F | 協作 | optional，列相關的人 |
| G | 優先級 | P0 / P1 / P2 / P3 |
| H | 狀態 | Pending / Waiting / Ongoing / done / backlog |
| I | 進度% | 自評 0-100 |
| J | 起始 | date |
| K | 預計完成 | date |
| L | 實際完成 | date（填了才算 done） |
| M | 產出連結 | PR / Google Doc / Slack thread |
| N | 最後更新 | 自動（公式） |
| O | 逾期天數 | 自動（公式） |
| P | 本週投入 | 小時數，每週會議前負責人自評 |
| Q | 子任務 | 自由文字，列目前展開的子任務 |
| R | 歷程 | 累積多行（前綴時間），取代獨立「更新日誌」分頁 |
| S | 現況 | 這週的一句話狀態 |

**設計要點**：
- **狀態值用英文**（Pending / Ongoing / done）：給 AI agent 解析 regex 不會雜亂
- **「歷程」欄取代獨立日誌分頁**：每列累積多行自由文字（前綴時間），避免跨 sheet 查詢
- **「本週投入」用小時數不用 0-5 分**：小時能加總得出總工時，分數無法轉換

---

## 總覽儀表板（週會主畫面）

### 必備區塊

| 區塊 | 內容 |
|------|------|
| **統計窗口參數** | B3 = N 天（可調，大部分指標依此窗口計算） |
| **本週摘要** | 進行中 / 卡住 / 近 N 天完成 / 本週完成 / 逾期 / 7 天未更新 / 當前案數 |
| **每人負載** | 4 人 × [進行 / 卡住 / 逾期 / 當前案數] |
| **類型分布** | 類型 × [進行中 / 近 N 天完成] |
| **屬性分布** | 屬性 × [進行中 / 近 N 天完成] |
| **屬性 × 負責人** | 交叉表（進行中案數）— 看老闆案被誰接 |
| **類型 × 投入** | 類型 × [投入總分 / 進行中案數] |
| **屬性 × 投入** | 屬性 × [投入總分 / 進行中案數] |
| **分類分布** | 分類 × [投入總分 / 進行中案數] |
| **團隊指標** | 見下 |

### 團隊指標（量化判讀基礎）

| 指標 | 怎麼算 | 判讀什麼 |
|------|-------|---------|
| **紮實 / 探索比** | 基礎建設佔比 vs 主題分析佔比 | 團隊重心偏哪邊 |
| **老闆案佔比** | 屬性為老闆 A/B 的案數 / 當前案數 | 自主性 vs 被動接案 |
| **P0 密度** | P0 案數 / 當前案數 | 緊急程度 |
| **急件比例** | 分類含「急」的案數 / 當前案數 | 規劃 vs 救火 |
| **Ad-hoc 佔比** | 臨時需求佔比 | 被動程度（過高 = 難以規劃） |
| **Dev / Maintenance 比** | 新造 vs 維運 | 建設中 vs 維持中 |
| **完成率 / 取消率 / 平均逾期天數** | — | 執行力 |
| **人均在手案數** | — | 判斷過載 |

**鐵則**：質性判讀交給 AI 月報分析（「團隊性格」），**累積 2-3 個月資料後才穩定**。前期數字不要過度解讀。

---

## 個人視圖（用 Google Sheets Filter View，不建分頁）

**設計**：
- 不建 xlsx 分頁、不用 QUERY → 避免分頁膨脹與雙向綁定衝突
- 每人用 Google Sheets 原生 Filter View
- 命名 `<Name> 焦點`
- 篩「負責人 = 該人」+「狀態 ≠ done / cancelled」+ 依 優先級 / 逾期排序

**代價**：Filter View 無法從 xlsx 匯入 Google Sheets 時自動建立，**每人首次要手動設一次**。

**為什麼不建分頁**：
- 每人一個分頁 → 分頁膨脹
- QUERY 濾清單 → 複雜且易踩雙向綁定陷阱
- Filter View native、秒開切換

---

## 每週 snapshot JSON（diff 的基礎）

**檔名**：`output/snapshots/YYYY-Www_YYYY-MM-DD-HH-MM-SS.json`

**schema v4**：
```json
{
  "schema_version": 4,
  "snapshot_at": "2026-11-11T10:30:00+08:00",
  "week": "2026W45",
  "overview": {
    "metrics": { ... 團隊指標 ... },
    "loads": [ { "person": "A", "ongoing": 5, "blocked": 1 }, ... ]
  },
  "projects": [
    {
      "name": "<案名>",     // unique key
      "type": "...",
      "attr": "...",
      ...（主表 19 欄）
    }
  ],
  "update_log": [...],
  "flags": { ... }
}
```

**為什麼需要 snapshot**：
- 差異（diff）生週報：AI 讀兩週 snapshot 比對「新增 / 完成 / 卡住 / 推進 / 延期」
- 回溯：某週看起來過載，三個月前是不是也這樣？
- 不依賴 Google Sheets 歷史記錄（API 限制多）

---

## AI agent 分工（Phase 4）

| 產出 | 來源 | 頻率 |
|------|------|------|
| **週報** | 主表 + 兩週 snapshot diff + 更新日誌 | 每週 |
| **月報** | 4 週 snapshot + 團隊性格指標 | 每月 |
| **老闆需求盤點** | 屬性 = 老闆 的案列表 + 進度 | 上行需求前 |

**AI 讀寫途徑**：
- Google Sheets MCP（讀 / 寫）
- Apps Script 觸發 snapshot（寫 JSON 到 Drive）
- AI agent 直接讀 snapshot JSON 做 diff

---

## 「核心命題」與「不解決的問題」

**核心命題**：N 人 × M 案（共 N×M 案）的規模下，管理成本必須 **< 不管理的隱形成本**。

**明確不解決**：
- ❌ sprint / velocity / story point —— 儀式感對這規模是負擔
- ❌ workflow 權限 —— 4 人全開 edit
- ❌ 跟 PR / commit 綁 ticket —— 工程流程還沒複雜到需要
- ❌ 跨團隊可見 —— 這是**團隊內**工具，對外用別的途徑溝通
- ❌ 時間追蹤精細到分鐘 —— 「本週投入小時數」自評粒度就夠

---

## 四個 Phase 推進順序

| Phase | 內容 | 可獨立見效 |
|-------|------|-----------|
| **Phase 1** | 三 sheet 建起來（總覽 / 主表 / 更新日誌），人工填 | ✅ 週會立刻能用 |
| **Phase 2** | Apps Script 自動化 snapshot | ✅ 回溯能力建立 |
| **Phase 3** | 本週紀要 panel / 會議 note | ✅ 週會流程完整 |
| **Phase 4** | AI 生週報 / 月報 / 團隊性格 | ✅ 人工做不動的自動化補完 |

**鐵則**：Phase 1 做完**當天**就要能用於下次週會。不要為了 Phase 4 的「智能分析」而推遲上線。

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| 用 JIRA | 建 workflow 兩週、團隊沒人想填 | 改單一 Sheet |
| 多分頁 | 分頁膨脹、雙向綁定踩雷 | 三張固定 sheet，個人視圖用 Filter View |
| 「本週投入」用 0-5 分 | 無法加總 | 改小時數 |
| 狀態值中文 | AI agent regex 解析雜亂 | 英文狀態值 |
| 獨立「更新日誌」分頁 | 跨 sheet 查詢麻煩 | 整合進主表的「歷程」欄 |
| 案名不 unique | snapshot diff 對不上 | A 欄強制 unique key |
| 前兩個月想解讀「團隊性格」 | 數字太少還不穩 | 累積 2-3 個月再解讀 |
| 想做跨團隊版 | scope 膨脹 | 這是團隊內工具，對外用別的 |
| 等 Phase 4 做完才上線 | 一直沒真的用上 | Phase 1 做完當天就上線 |
| xlsx 範本 + 匯入 | 重複失真 | 直接把 Google Sheets 當真本 |

---

## 檢核清單（建完 tracker 前對一次）

- [ ] 三 sheet（總覽 / 主表 / 更新日誌）都建了嗎？
- [ ] 主表 19 欄齊了嗎？案名在 A 欄當 unique key？
- [ ] 狀態值用英文（Pending / Ongoing / done）？
- [ ] 「本週投入」用小時數不是分數？
- [ ] 總覽有「團隊指標」區（紮實/探索比、老闆案佔比...）？
- [ ] 每人一個 Filter View（不是分頁）？
- [ ] 每週 snapshot JSON 機制（Apps Script）建了嗎？
- [ ] snapshot schema 有 version 欄嗎？
- [ ] AI agent 能讀寫（Sheets MCP + Drive JSON）嗎？
- [ ] 核心命題寫清楚（N 人 × M 案 → 管理成本 < 不管理成本）？
- [ ] 明確「不做什麼」有列嗎（sprint / 跨團隊 / 時間追蹤分鐘）？

---

## 相關

- [[bi-knowledge-base-structure]] — 知識庫 vs tracker 不同層：這份是任務流，那份是知識沉澱
- [[claude-md-navigation-pattern]] — 給 agent 讀 repo 的入口；tracker 也可以放 CLAUDE.md
- [[incident-log-management]] — 任務的 lifecycle 也可以當事件簿
- [[handover-doc-skeleton]] — tracker 的使用交接文件用這份骨架

## 一句話總結

> **3-5 人團隊的管理成本必須 < 不管理的隱形成本**。用 Google Sheets 當單一真相源、每週 snapshot JSON 存檔、AI agent 補完自動化——取代 JIRA 但保有可量化分析，所有人只在 Sheets 上作業。
