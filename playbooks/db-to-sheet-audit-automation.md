---
title: DB → Google Sheet 自動化稽查流程 playbook
version: v1
last-updated: 2026-11-04
source: govern_routine_work（去識別化）
---

# DB → Google Sheet 自動化稽查流程 playbook

> 主管機關或內控稽查需求：給 N 份 Google Sheet 範本，要從 DB 把特定時間窗口的 N 類紀錄填進去。看起來簡單，實際有：config 三處要同步、窗口外 fallback 規則、OAuth scope、API rate-limit、sheet 結構不可動…。這份文件給一條完整流程。

## 情境（什麼時候拿出來用）

- 收到稽查需求信（主管機關／內控／法遵）
- 每月／每季要把 DB 查到的紀錄填進多份 Google Sheet
- Sheet 範本結構固定、不可動（註 / marker / 格式）
- 要做到「可重跑、可 dry-run、可追蹤」

## 核心主張

1. **收需求就先結構化**（三類資訊：窗口、對象、過濾）
2. **三個 config 同步**（JSON × 2 + SQL CTE）
3. **窗口外 fallback 規則**明文（主管機關要「最近 1 筆」）
4. **先 dry-run 再推**
5. **OAuth scope 最小化**（`drive.file` 而非 `drive`）
6. **Rate-limit 自動 retry**

---

## 流程 8 步

### Step 1：收需求信並結構化

需求通常是文字描述，先拆成三類資訊：

| 類別 | 內容 | 範例 |
|------|------|------|
| **時間窗口** | 稽查月份與起訖日 | 2026-07-05 ~ 2026-07-11 |
| **對象清單** | 車牌／門市／帳號等 N 個 | 15 台車 × 1 窗口 |
| **過濾條件** | 子類別、里程、必填欄位 | subtype 排除、里程範圍 |

**特別注意**：
- 若信附新 Sheet 範本 → 核對章節結構（header 位置、marker、註）是否跟歷史版本一致
- 有變動 → 同步改 script 的 anchor
- 若有新過濾條件 → SQL 的 WHERE 與 push script 的 filter 都要改

### Step 2：更新三個 config（必須同步）

```
1. scripts/sheet_map.json          對象 → Spreadsheet ID
2. scripts/plate_windows.json      對象 → {start, end} 窗口
3. N 支 SQL 內的 plate_window CTE  (對象, 窗口起, 窗口迄)
```

**鐵則**：三處的對象與日期**必須完全一致**。不一致會導致：
- push 失敗（沒對應 sheet）
- 資料錯位（SQL 跑一個時段、push 檢查另一個時段）

### Step 3：DB 取數（N 支 SQL）

一個資料類別一支 SQL，共用 CTE 架構：

```sql
WITH plate_window AS (
  SELECT * FROM (VALUES
    ('對象 1', DATE '起', DATE '迄'),
    ...
  ) AS t(key, start_dt, end_dt)
)
, boundary_before AS (     -- 窗口前最後一筆
  SELECT key, MAX(事件日) AS dt_before
  FROM plate_window p JOIN 事件表 t ON t.key = p.key AND 事件日 <= p.start_dt
  GROUP BY key
)
, boundary_after AS (      -- 窗口後第一筆
  SELECT key, MIN(事件日) AS dt_after
  FROM plate_window p JOIN 事件表 t ON t.key = p.key AND 事件日 >= p.end_dt
  GROUP BY key
)
, plate_range AS (         -- 擴到含跨界的整日
  SELECT key,
         LEAST(COALESCE(dt_before, start_dt), start_dt) AS range_start,
         GREATEST(COALESCE(dt_after, end_dt), end_dt)   AS range_end
  FROM plate_window p
  LEFT JOIN boundary_before bb USING (key)
  LEFT JOIN boundary_after  ba USING (key)
)
SELECT ...
FROM plate_range pr
JOIN 事件表 t ON t.key = pr.key AND 事件日 BETWEEN pr.range_start AND pr.range_end
```

**boundary 邏輯語意**：
- 目的：對應稽查模板「如無紀錄，請提供最近 1 筆」
- 做法：窗口外**以整日為單位**外推
- 副作用：外推日有多筆事件時全部進，不只 1 筆（刻意保留）

**第一次跑先小樣本驗 schema**（欄名、型別、encoding）。

### Step 4：下載 CSV

- 編碼 **UTF-8**（含 BOM 可）
- 多行欄位（如工單描述）必須用**雙引號**包
- 檔名帶日期戳（便於追溯）

### Step 5：準備 Google Sheet

**最容易卡的一步**：

1. 收齊 N 份 sheet 連結
2. 每份都對**服務帳號 email** 開啟「編輯者」權限
3. 否則 Sheets API 寫入會 **403**
4. Tab 名、章節結構（header 位置、marker、註）**不要動**
5. Sheet 名建議維持 `MM/DD~MM/DD_<key>` 便於辨識

**OAuth scope 限制**：
- `drive.file` 無法列資料夾 → N 個 Spreadsheet ID 必須**人工收集**後更新 `sheet_map.json`
- 如需列資料夾 → 要申請 `drive.readonly`（權限更大，應避免）

### Step 6：Dry-run 檢查

```bash
python3 scripts/push_to_sheets.py --csv data/<trip>  --dry-run
python3 scripts/push_maint_repair.py --maint <保養> --repair <維修> --dry-run
```

**檢查**：
- 所有對象都有對應 sheet？
- 沒有 anchor missing 錯誤？
- marker 位置合理？
- 要 insert 幾列、寫入範圍符合預期？

Dry-run 不過 → 回 Step 2 修 config 或 Step 3 修 SQL。

### Step 7：正式推送

拿掉 `--dry-run` 重跑同樣命令。

**可能遇到 429 rate-limit**（Sheets API 60 req/min）：
- script 內建自動 retry
- 建議 backoff：15 → 30 → 60 → 120 → 240 → 480s（最多 6 次）

### Step 8：肉眼抽驗

開 2-3 份 sheet 檢查：
- 第 X 列 header 沒被動到
- 資料筆數對（全給 or 按窗口 + fallback 規則）
- 格式邊框完整
- 下方 marker 與註都還在

有問題：改完回 Step 3 或 Step 6 重跑。

---

## 窗口外 fallback 規則

稽查模板常寫「如無紀錄，請提供最近 1 筆」。做法：

| 類別 | 窗口內 | 窗口內無紀錄 | CSV 完全沒這對象 |
|------|-------|-------------|----------------|
| A（含外推） | 全部寫入 | 用 SQL boundary 外推帶出 | 寫空白 |
| B（二次篩選） | 全部寫入 | 挑一筆**離窗口最近**的（before/after 皆可，絕對日數最小，相同距離取較晚），寫 1 筆 | 區段寫空白 |

**命門**：這條邏輯要寫在 **push script**（SQL 全給，push 篩選），因為：
- SQL 做主篩選 → 難處理「離窗口最近」
- Push 層次單純 → 較易處理複雜 fallback

---

## 檔案結構

```
project/
├── README.md                              入口
├── sql/
│   ├── <type_A>_audit_<period>.sql        第 N 期 SQL
│   └── ...
├── scripts/
│   ├── sheet_map.json                     對象 → Spreadsheet ID
│   ├── plate_windows.json                 對象 → 窗口
│   ├── push_<type_A>.py                   推送 A 類
│   └── push_<type_B_C>.py                 推送 B+C 類（併送）
└── data/
    ├── <date_tag>_<type>_data.csv         CSV
    └── sample/                            schema 樣本（DB 欄位對照用）
```

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| 三處 config 不一致 | push 失敗或錯位 | 更新時三處同步 |
| 直接正式推送 | 範圍錯要重做 | 一定先 dry-run |
| Sheet 未授權 | API 403 | 對服務帳號開「編輯者」 |
| 動 Sheet 章節 | anchor missing | 保留 header 第 N 列、marker、註 |
| scope 太大 | 權限審查難過 | 用 `drive.file` 不用 `drive` |
| 不處理 rate-limit | 中途失敗 | 自動 retry with backoff |
| 窗口內有紀錄但額外帶一筆 | 多寫一筆 | fallback 只在「窗口內無」時觸發 |
| SQL schema 第一次直接跑全量 | 跑半天發現欄名錯 | 先小樣本驗 schema |
| 沒抽驗就報完工 | 格式被動到不知 | 肉眼抽 2-3 份 |
| 檔名沒日期 | 版本混亂 | 固定格式帶日期戳 |

---

## 檢核清單

- [ ] 需求信三類資訊拆完（窗口 / 對象 / 過濾）？
- [ ] 三個 config（sheet_map / plate_windows / SQL CTE）同步？
- [ ] SQL 用 boundary CTE 處理窗口外 fallback？
- [ ] CSV UTF-8 + 雙引號包多行欄位？
- [ ] Sheet 對服務帳號開編輯者權限？
- [ ] Sheet 章節結構保留？
- [ ] Dry-run 過了？
- [ ] Rate-limit 自動 retry 建置？
- [ ] 推送後肉眼抽 2-3 份驗？
- [ ] OAuth scope 最小化？

---

## 相關

- [[data-flow-playbook-skeleton]] — DB 端的資料源在 F1/F2 層
- [[multi-track-analysis-management]] — 若多類稽查併跑時的管理
- [[government-api-integration]] — 稽查資料常要配政府法規參考，是對面流程

## 真實案例骨架（去識別化）

### 案例 1：三處 config 不同步
開發者改了 SQL 的對象清單但沒改 `sheet_map.json`。跑完 dry-run 報 15 個對象 missing。花 30 分鐘追才發現。
**校正**：寫一個 `verify_configs.py` 跑 pre-commit 驗三處一致。

### 案例 2：Sheet 範本改了但 script 沒改
新季的 Sheet 範本第 7 列 header 改成第 8 列。推送後所有資料寫錯位。
**校正**：Step 1 收新範本就核對章節結構，發現變動同步 script anchor。

### 案例 3：429 rate-limit 中斷
15 份 sheet 推到第 8 份失敗。原本沒 retry。改成指數 backoff 後穩定跑完。

### 案例 4：窗口內有紀錄還多寫一筆
fallback 邏輯誤判，某台車窗口內有 3 筆記錄還額外寫了 1 筆最近的。
**校正**：邏輯順序改成「先看窗口內有無 → 有則不 fallback」。
