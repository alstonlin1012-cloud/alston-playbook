---
title: NL → SQL → LLM 解釋 agent 分層設計
version: v1
last-updated: 2026-11-04
source: sales-pulse-agent（去識別化）
---

# NL → SQL → LLM 解釋 agent 分層

> 讓業務用自然語言問 BI 問題、agent 回答數字。最常見的錯：把「計算」交給 LLM 自己處理（讓 LLM 讀整張表自己算）。這份文件說明怎麼分層：LLM 寫 SQL（翻譯層）、DB 算（計算層）、LLM 解釋（寫作層）。

## 情境（什麼時候拿出來用）

- 要做內部 BI 問答機器人
- 業務／門市主管要能直接問「我上週 X 多少」
- 想取代「要工程師寫 SQL」的常態
- 有結構化資料倉（BQ／Snowflake／Postgres）

## 核心主張

**三層分工**，每層只做一件事：

| 層 | 誰做 | 做什麼 | 不做 |
|----|------|-------|-----|
| **翻譯層** | LLM #1（強 model） | NL 問題 → SQL | 算數字 |
| **計算層** | DB 本身 | 執行 SQL、精確計算 | 處理 NL |
| **解釋層** | LLM #2（快 model） | 結果 → 人話解釋 | 驗證計算 |

**反模式**（常見錯誤）：
- 把整張 table 倒進 LLM prompt 要它「自己算」 → 不準、慢、貴
- 讓 LLM 寫作同時又算數字 → 兩件事混在一起品質都差

**正模式**：
- LLM #1 專心翻譯：NL → SQL
- DB 專心計算：精確、可稽核
- LLM #2 專心寫作：結果 → 業務可讀的解釋

---

## 架構圖

```
使用者提問（NL）
    │
    ▼
【LLM #1】generate_sql(question, schema, business_context) → SQL
    │
    ▼
【DB】execute_sql(sql) → rows / aggregates
    │
    ▼
【LLM #2】explain(question, rows, context) → NL 解釋
    │
    ▼
使用者看到：數字 + 解釋 + SQL（debug 用可選開）
```

---

## 三個常見資料路徑（容易混淆）

寫 BI app 時常有這三條路徑，**不要混**：

### 路徑 A：儀表板取數（結構化圖表）
```
固定 SQL → DB → JSON → 前端渲染圖表
```
- 固定 SQL，不走 LLM
- 這條 OK，不要動

### 路徑 B：AI 報告產生器
```
前端算好的 metrics → LLM prompt → 散文報告
```
- LLM 做**寫作**，不做**計算**
- 彙總是前端算好的
- 這條 OK，**不是問答品質差的原因**

### 路徑 C：問答機器人（本 pattern 的核心）
```
NL → LLM #1 寫 SQL → DB → LLM #2 解釋
```
- 這條是 NL→SQL pattern
- 若這條做錯（整張 table 倒進 LLM 要它算）會很爛

**鐵則**：**三路徑職責分清**，不要用一條路徑解所有問題。路徑 B 寫得好 ≠ 問答機器人好；問答爛要修的是路徑 C，不是把路徑 B 塞更多資料。

---

## 分工細節

### LLM #1（翻譯層）

- **模型選擇**：用強 model（寫 SQL 要精準）
- **輸入**：
  - 使用者問題（NL）
  - Schema（table、column、type）
  - Business context（canonical 定義、SQL cookbook 範例）
- **輸出**：SQL（非 streaming、一次產出）
- **驗證**：
  - 跑 dry-run 或限樣本試跑
  - 檢查 SQL 語法、表名／欄名合法

### DB（計算層）

- 執行 SQL、精確計算
- 回傳 rows 或 aggregates
- **size 控制**：加 LIMIT／aggregate，避免把整張表吐回
- Cache：常見問題結果可 cache（快、省 LLM 費用）

### LLM #2（解釋層）

- **模型選擇**：用快 model（寫作成本敏感、容錯）
- **輸入**：
  - 使用者原問題
  - DB 回傳的 rows / aggregates
  - Business context
- **輸出**：NL 解釋（streaming 或三段式）
- **驗證**：確認輸出的數字跟 rows 一致（LLM 不要瞎編）

---

## 常見陷阱

### 陷阱 1：讓 LLM 看整張 table 自己算

**症狀**：
- 前端或後端 `SELECT * FROM table` 把整張表倒進 LLM
- Prompt 長到 100KB+
- 數字算錯、常常偏差

**校正**：
- **絕對不要** `SELECT *`
- LLM #1 必須產出**有 aggregate / filter / limit 的 SQL**
- DB 回傳**聚合後**的結果

### 陷阱 2：Key 在前端 bundle

**症狀**：
- 前端直接呼叫 Gemini / OpenAI API
- API key 打包進 bundle（例：Vite `define` 字面值替換）
- `dist/` 內明文出現 key
- IAP 只能限制誰「開 app」，key 一旦被取出 IAP 外可用

**校正**：
- API key **只在後端持有**
- 前端只呼叫**自家後端的 API**，後端再呼叫 LLM
- 搬到後端後**立即 rotate** 舊 key

### 陷阱 3：SQL eval 題庫寫死數字

**症狀**：
- eval 題庫：「問題 X、預期答案 Y」
- 資料每天變，昨天對的今天錯
- eval 看起來 fail 不是 agent 爛，是資料漂移

**校正**：
- 題庫存**參考 SQL**，而非寫死數字
- Eval 跑時：先跑參考 SQL 取 ground truth，再跑 agent 比對
- 這樣資料漂移不會污染 eval

### 陷阱 4：Streaming 做過頭

**症狀**：SSE 逐字渲染解釋，但 LLM #1 先跑完 SQL、再跑 DB、再跑 LLM #2。使用者前 5 秒看不到任何進度。

**校正**：
- **三段式進度提示**：「正在產 SQL... → 正在查 DB... → 正在整理回覆...」
- LLM #2 的解釋**可以 streaming**，但前面兩段不是

### 陷阱 5：沒有 business context 層

**症狀**：
- 業務問「上週活躍用戶」
- LLM 不知「活躍」是 DAU、是週 retained、是某指標
- 寫出來的 SQL 口徑不對

**校正**：
- 建 `business_context`：canonical 定義 + SQL cookbook + schema 註記
- LLM #1 的 prompt 包含相關 context 片段
- 接 BI knowledge base（見 [[bi-knowledge-base-structure]]）

---

## 分階段改造 workflow（若接手改造現有 app）

常見情境：已有前端跑 LLM 的 BI app，要搬到後端。

```
MR-0: 盤點前端現有邏輯（go/no-go gate）
       - 三條路徑分清
       - 哪些是寫作、哪些是計算
       - 找 API key 位置

MR-1: Schema 與業務口徑盤點
       - 列出會被問到的 table / column
       - 列 canonical metric 定義
       - 準備 business_context

MR-2: 新建後端服務（agent）
       - LLM #1 + DB + LLM #2
       - eval 題庫

MR-3: 前端切換（調 API endpoint）
       - 可能只改幾十行、不重寫

MR-4: 驗證題庫 + 部署
       - eval 綠才上

MR-5: 報告產生器後端化 + Key rotate
       - 寫作類也搬到後端
       - 舊 key rotate
```

**鐵則**：
- **一個 MR 一次**，每個 MR 有 acceptance criteria
- MR-0 是 go/no-go gate，別跳過
- API key rotate 要等**所有**前端用 key 的點都搬完

---

## 檢核清單

- [ ] 三條路徑（儀表板／報告／問答）分清？
- [ ] LLM #1 只翻譯、不算數字？
- [ ] DB 專心計算、回傳 aggregate？
- [ ] LLM #2 只寫作、不驗算？
- [ ] API key 只在後端？
- [ ] eval 題庫存參考 SQL 而非數字？
- [ ] 進度提示三段式（非盲等）？
- [ ] business_context 層有嗎？
- [ ] LLM #1 用強 model，LLM #2 用快 model？
- [ ] 分階段改造的 MR 序列有嗎？

---

## 相關

- [[bi-knowledge-base-structure]] — business_context 層的來源
- [[data-flow-playbook-skeleton]] — DB 端的 F1-F4 整合
- [[offline-build-static-json-pattern]] — 若問答結果可快取為靜態 JSON

## 真實案例骨架（去識別化）

### 案例 1：前端 `SELECT *` 倒 32MB 進 LLM
原本「問答機器人」直接 `SELECT * FROM Store` + `SELECT * FROM Product` 把整張表倒進 LLM prompt，32MB payload 進瀏覽器。
**校正**：LLM #1 產**聚合 SQL**（`SELECT city, SUM(...) ... GROUP BY ...`）、DB 回傳 100 列以內、LLM #2 解釋。prompt 從 32MB 降到 < 50KB，反應時間從 20s 降到 3s。

### 案例 2：API key 在前端 bundle
Vite `define` 做字面值替換，build 後 `dist/*.js` 明文出現 key。IAP 擋得了 app 開啟，擋不了 key 被複製走。
**校正**：MR-3 前端切換到打自家後端、MR-5 完成後 rotate 舊 key。注意 rotate 前要**所有**前端用 key 的地方都搬完，否則報告功能會掛。

### 案例 3：eval 題庫寫死數字 → 資料漂移誤判
原本 eval：「問題 Q1 → 預期答案 100 台」。資料每天變，某天真實答案 110 台，agent 回 110，被判「錯」。
**校正**：改存「參考 SQL」。eval 跑時先跑參考 SQL 得 ground truth，再比對 agent 結果。資料漂移不影響。

### 案例 4：Region 錯誤
`gemini-2.5-pro` 用 `asia-east1` region 會 404。該 region 不供 Gemini 2.5。
**校正**：改 `asia-northeast1`。提醒：新 model region 支援可能滯後，先 doc 查。
