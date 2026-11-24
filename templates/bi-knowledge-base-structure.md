---
title: BI 知識庫結構 — 讓人跟 AI Agent 都能自助查答
version: v1
last-updated: 2026-11-03
source: bi-knowledge-base（去識別化）
---

# BI 知識庫結構

> BI 團隊常見痛點：資深同事腦內有太多隱性知識，新人上手慢、AI agent 無法自主查答、業務問同一題三次得到三個答案。這份文件給一個 **人 × AI agent 共用知識庫** 的目錄結構與維運邏輯。

## 情境（什麼時候拿出來用）

- BI 團隊想建知識庫（取代「問資深同事」）
- 想讓 AI agent（text-to-SQL、分析 agent）有 context 可查
- 業務指標在不同人口中有不同定義，要收斂到 single source of truth
- 新人上手要兩個月才上手，想降到兩週

## 核心主張

- **人跟 AI 讀同一套檔**，不是「人看網頁、AI 看另一份」
- AI agent 從 `index.md` 的一句話摘要決定載哪些檔
- 文件品質直接影響 AI 判斷準確度 → **摘要描述要具體**
- 四大分區（Business Context / Data Library / Playbook / Agent Skills）各管一塊
- 用 MkDocs + 靜態站 + IAP 存取（不自己做 permission）

---

## 四大分區

```
docs/
├── index.md                       網站首頁 + Agent 入口
├── Business_context/              業務背景與指標定義
│   ├── 00-company-overview/
│   ├── 01-financial-overview/
│   ├── 02-market/
│   ├── 03-RS/ (零售銷售)
│   ├── 04-AS/ (售後服務)
│   └── 05-xxx/ (其他事業體)
├── Data_library/                  資料管線、字典、血緣
│   ├── 01_data_sources/
│   ├── 02_data_pipeline/
│   └── 03_data_lineage/
├── Playbook/                      BI 開發原則、流程指南
│   ├── BI_developer/              開發者指南
│   │   ├── 10-webapp/
│   │   └── 11-projects/
│   ├── BP_planner/                業務夥伴指南
│   ├── Report_repair_guide/       報表故障修復
│   └── AI_agents/                 AI agent 使用指南
└── Agent_skills/                  AI agent 可用的 skill 清單
    └── tools/                     MCP 工具說明
```

### 分區職責

| 分區 | 回答什麼 | 誰維護 | 誰讀 |
|------|---------|-------|------|
| **Business Context** | 業務邏輯、指標 canonical 定義、商業流程 | BI + 業務協作 | 分析師、AI、新人 |
| **Data Library** | 資料從哪來、怎麼算、改欄位會壞什麼 | BI data eng | 分析師、AI、下游 workbook owner |
| **Playbook** | 遇到問題怎麼做（開發、修報表、計畫） | 各角色 lead | 執行者 |
| **Agent Skills** | AI 可用的工具／skill 入口 | BI | AI agent（主）、人（參考） |

---

## 四大設計原則

### 原則 1：index.md 是摘要層，不是 TOC

每個分區（每層目錄）都有 `index.md`。AI agent 第一步讀 `index.md`，從摘要判斷哪些檔案跟當前任務有關。

**壞寫法**：
```markdown
# 零售銷售

本區包含：
- customer.md
- order.md
- promotion.md
```

**好寫法**：
```markdown
# 零售銷售 (RS)

零售銷售業務的漏斗流程與指標定義，涵蓋流量、潛客、訂單等各階段的業務語意與數據口徑。

## 內容
- `customer.md` — 顧客生命週期（新客／既有客／沈睡客）定義、各階段轉換率計算公式、常見判定陷阱
- `order.md` — 訂單狀態機（下訂／付款／退款）、各狀態的業務意涵、訂單時間戳 vs 領牌時間戳的分辨
- `promotion.md` — 促案種類（補貼／加碼／組合包）、對 contribution margin 的影響、常見 cannibalization 陷阱
```

**AI 讀第二份摘要後**：能具體決定「我現在在算轉換率，載 `customer.md`，不載 `order.md`」。

### 原則 2：摘要是契約

- 摘要寫錯，AI 載錯檔
- 檔案改內容，摘要必須同步改
- 每份 md 的頭 3 行就是它的「廣告語」

### 原則 3：Business Context ≠ Data Library

**Business Context**：寫業務語言、業務邏輯、什麼叫「活躍用戶」
**Data Library**：寫 table schema、血緣、計算 SQL

兩者**互相引用**但不混寫。業務同事看 Business Context，不會打開 Data Library。

### 原則 4：Playbook 是流程，不是知識

- Business Context 答「什麼是」
- Playbook 答「怎麼做」
- 遇到問題要修報表 → Playbook
- 遇到不懂業務邏輯 → Business Context

---

## AI Agent 讀取流程（典型三步）

```
Step 1: 讀 docs/index.md
        → 取各分區的一句話摘要
        → 判斷哪些分區跟當前任務相關

Step 2: 讀相關分區的 index.md
        → 從檔案摘要列表決定載哪些 .md

Step 3: 載對應 .md 的完整內容為 context
        若需執行工具 → 從 Agent_skills/tools/ 載對應規格
```

**關鍵**：**AI agent 直接讀原始 .md，不透過網頁**。網頁是給人看的；AI 讀原始碼。

---

## 技術架構（MkDocs + IAP + GCS）

```
使用者（瀏覽器）
    ↓ HTTPS
Load Balancer + IAP（既有身份驗證）
    ↓ 通過驗證
Cloud Run（純 file server，從 GCS 讀檔回傳）
    ↓
GCS bucket（私有，存放 MkDocs 靜態 HTML）
```

**設計要點**：
- **MkDocs 做靜態 HTML**：寫 Markdown 就好，不碰前端
- **IAP 管身份**：用公司既有 Google 帳號登入，不自己做 permission
- **GCS 存靜態檔**：便宜、不用維運
- **Cloud Run 純 file server**：不做驗證（IAP 已做）
- **CI/CD 自動部署**：Merge MR 後幾分鐘自動更新

### 寫文件體驗

- 編輯 `docs/<path>/<file>.md`
- 開 Merge Request
- Review merge 後自動部署
- 幾分鐘內網站更新

### nav 自動同步

- `nav_config.yml`：資料夾顯示名稱對照表
- `sync_nav.py`：掃 `docs/` 自動產出 `mkdocs.yml` 的 nav 區塊
- **寫新目錄不需要手動改 nav**

---

## 文件撰寫規範

### 每份 md 的 header 三行

```markdown
# [文件標題]

[這份文件回答什麼問題。一句話。具體到 AI 讀完能判斷要不要載]

[如果這份文件有「適用邊界」，第二句話明說]

---

[正文...]
```

### 業務指標的 canonical 定義模板

```markdown
## [指標名]

**一句話定義**：... 

**canonical SQL**：
```sql
SELECT ...
```

**計算口徑**：
- 分子：...
- 分母：...
- 排除：... (例：test 車輛)

**典型用途**：...

**常見混淆**：
- 跟 X 不一樣：... （避免同名不同義）
- 跨期比較要注意：...

**血緣**：[`lineage/<table>.yaml`](...)
```

### 跨檔引用規範

- 用相對連結：`[指標字典](../Data_library/metrics.md)`
- 用統一術語：若業務說「活躍」而 data 說「DAU」，字典統一命名
- 若兩個概念相關但不同，各給一行說明差別

---

## 不要做

### 不要把 AI agent 廠商名寫進對外文件

**原因**：公司政策不希望知識庫指名特定廠商。

**替代詞**：

| 原詞 | 替代 |
|------|------|
| 廠商產品 CLI（Claude Code / Cursor 等） | `Agent CLI` / `AI Coding Agent CLI` |
| 廠商網頁版 | `AI 對話網頁介面` |
| 廠商品牌當主詞 | `agent` / `AI 助手` |

**例外**：工具寫死的 config 路徑（`.claude/`、`.cursor/`）、第三方 repo 名、skill 內部必需字串。

### 不要在 main branch 直接 commit

- 所有變更走 MR
- Branch 命名：`feat/...`、`fix/...`、`docs/...`
- Review merge 後自動部署

### 不要在知識庫塞 raw data

- 知識庫只放**定義、邏輯、流程**
- 不放 raw data、不放 PII、不放未脫敏的業務數字

### 不要重複

- 一個指標只有一個 canonical 定義
- 其他地方只能**引用**，不能複製
- 若發現兩個地方寫同一指標，收斂到一處

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| index.md 只列檔名 | AI 載不出對的檔 | 寫一句話具體摘要 |
| 業務 context 寫成 schema | 業務看不懂 | 分 Business Context vs Data Library |
| Playbook 寫成 FAQ | 流程不連貫 | Playbook 是「怎麼做」步驟 |
| 同指標多定義 | 業務三次得三答 | canonical 定義集中到字典 |
| 文件改內容忘改摘要 | AI 繼續載舊檔 | 摘要是契約，必須同步 |
| nav 手動維護 | 新目錄沒上線 | sync_nav.py 自動化 |
| 把 permission 寫進 app | 維運痛苦 | 用 IAP 統一管 |
| 把 AI 廠商名寫進對外文件 | 公司政策違反 | 用 `agent` 等泛稱 |

---

## 檢核清單（建 BI KB 前對一次）

- [ ] 四分區（Business / Data / Playbook / Agent Skills）清楚了嗎？
- [ ] 每層目錄有 `index.md` 嗎？
- [ ] index.md 摘要是一句話＋具體嗎（AI 讀完能判斷載不載）？
- [ ] canonical 指標定義集中了嗎？
- [ ] 跨檔引用用相對連結？
- [ ] nav 自動化（sync 工具）了嗎？
- [ ] 身份驗證走 IAP 不自己做？
- [ ] MR workflow 建立了嗎？
- [ ] 新人跑一次能靠文件自助找到答案嗎？
- [ ] AI agent 跑一次能靠文件回答 60-70% 的 BI 問題嗎？

---

## 相關

- [[data-flow-playbook-skeleton]] — Data Library 的血緣檔格式
- [[verifiable-judgment-framework-writing]] — 業務指標定義裡的判準照 meta 規則
- [[funnel-ranking-diagnosis]] — Business Context 的漏斗指標範例

## 真實收益（去識別化）

### 收益 1：新人上手時間
原本問資深同事「活躍用戶怎麼算」要 1-3 天來回。有 BI KB 後：新人讀 `index.md` → 讀 `metrics.md` → 5 分鐘能自己算。

### 收益 2：AI agent 可答 60-70% 的業務問題
text-to-SQL agent 讀 BI KB 的 `Business Context` + `Data Library`，就能回答大多數業務同事問題，不用人工 handle。

### 收益 3：指標定義不漂移
同一指標跨 workbook／報告有統一定義。業務不再「問三個人得三答」。

### 收益 4：改欄位的衝擊可預估
IT 要改 raw schema 時，BI 可用「反查 lineage」立刻列出受影響 workbook 清單，提前通知。

---

## 專案驗收條件

建完一個 BI KB，驗收時跑這幾個情境：

1. **新人上手測試**：找一個入職 2 週的分析師，問 10 題業務問題，看能靠文件答出幾題
2. **AI 查詢測試**：text-to-SQL agent 丟 10 題業務問題，看回答對幾題
3. **指標一致測試**：同一指標 cross-reference 3 份報告，數字應該一致
4. **血緣反查測試**：假設改一欄 raw，看能否 5 分鐘內列出受影響 workbook
5. **nav 自動測試**：新建一個目錄 + md，看 CI/CD 後能否在網頁 nav 看到
