---
title: 資料流 playbook 骨架 — F1-F4 四層 single source of truth 架構
version: v1
last-updated: 2026-11-03
source: gsh_data_playbook（去識別化）
---

# 資料流 playbook 骨架

> BI 團隊常見痛點：欄位哪來的？改這欄會壞什麼？Tableau 數字為什麼和 DB 不一樣？這份骨架設計一個 **four-layer data flow playbook**，讓人跟 AI 都能自助查答，不用去問資深同事。

## 情境（什麼時候拿出來用）

- BI 團隊剛成立，想建 single source of truth
- 常被業務問「某數字怎麼算」、「某欄位哪來」
- 想把資深同事腦裡的血緣知識外化
- 要做 metrics dictionary、SQL cookbook
- 想讓 AI agent（例：text-to-SQL）有語義層可查

## 核心主張

**資料不是流到報表，是**流過四層**，每一層有不同擁有者、不同職責、不同下游**：

```
F1          F2            F3                    F4
Source ──> Raw      ──>  Analytic             ─> Presentation
系統       原始落地       整理 / 聚合            BI 工具 / Dashboard
```

- 每一箭頭有明確擁有者
- 每一箭頭有「血緣記錄」檔
- 每一箭頭的失敗／變動有通知路徑
- 每一箭頭都可反查

---

## 四層標準架構

### F1：Source → Raw（來源層 → 原始層）

| 項目 | 內容 |
|------|------|
| 誰擁有 | IT／資料工程 |
| 轉換 | 業務系統寫入 |
| BI 角色 | **只讀**，不改 |
| 文件位置 | `schemas/raw/<table>.yaml` |
| 變更通知 | IT → BI |

### F2：Raw → Analytic（原始層 → 整理層）

| 項目 | 內容 |
|------|------|
| 誰擁有 | BI |
| 轉換 | ETL（py / SQL job） |
| 做什麼 | 欄位重新命名／join 多張寬表／聚合（daily / monthly）／加業務規則 |
| 原始碼 | `transforms/F2/<analytic_table>.{sql,py}` |
| 血緣檔 | `lineage/<analytic_table>.yaml` |
| 文件位置 | `schemas/analytic/<table>.yaml` |
| 變更通知 | BI → 業務（指標會變） |

### F3：Analytic → Datasource（整理層 → 資料源）

| 項目 | 內容 |
|------|------|
| 誰擁有 | BI |
| 轉換 | Datasource SQL（Tableau／Looker／PowerBI 內的 SQL） |
| 原始碼 | `transforms/F3/<datasource>.sql` |
| 索引 | `tool/datasources.yaml`（status / schedule / sources） |
| 自動化 | `scripts/fetch_f3.py` 定期 snapshot |
| 變更通知 | BI → workbook owner |

### F4：Datasource → Workbook（資料源 → 呈現層）

| 項目 | 內容 |
|------|------|
| 誰擁有 | Workbook owner（可能是業務、PM、BI） |
| 轉換 | 計算欄位（calc field）+ 視覺化 |
| 文件位置 | `tool/calc_fields/<workbook>.md` |
| 變更通知 | workbook owner → 業務 |

---

## 骨架的目錄結構

```
data-playbook/
├── README.md                           ← 入口
├── docs/
│   ├── PRD.md                          專案背景 + roadmap + 執行紀錄
│   ├── 00_data_flow.md                 本頁（四層總覽）
│   ├── 05_metrics_dictionary.md        業務指標字典（canonical 定義）
│   ├── 06_sql_cookbook.md              常見問題 ready-to-copy SQL
│   └── 07_sanitization_process.md      血緣抽取流程 SOP
├── schemas/
│   ├── raw/<table>.yaml                F1 層 schema
│   └── analytic/<table>.yaml           F2 層 schema
├── lineage/
│   └── <analytic_table>.yaml           F2 血緣（source_tables / transformations / used_by）
├── transforms/
│   ├── F2/<analytic_table>.{sql,py}    F2 ETL 原始碼
│   └── F3/<datasource>.sql             F3 datasource SQL snapshot
├── tool/
│   ├── datasources.yaml                F3 datasource 索引
│   ├── calc_fields/<workbook>.md       F4 計算欄位記錄
│   └── workbooks/<workbook>.yaml       F4 workbook 索引
└── scripts/
    └── fetch_f3.py                     自動 snapshot F3
```

---

## 五個核心問答表（人與 AI 都用）

這五個問答覆蓋 90% 的日常詢問：

| 問題 | 看哪裡 |
|------|-------|
| 這張 analytic table 怎麼來的？裡面欄位什麼意思？ | `lineage/<table>.yaml` + `schemas/analytic/<table>.yaml` |
| 某業務指標（週轉率、UTR、GMV…）的 canonical 定義？ | `docs/05_metrics_dictionary.md` |
| 某指標的 SQL 怎麼寫？ | `docs/06_sql_cookbook.md` |
| 某 workbook 用到哪張 table？寫了什麼 calc field？ | `tool/calc_fields/<workbook>.md` + `tool/workbooks/<workbook>.yaml` |
| 改某 raw 欄位會壞什麼？ | 反查 `lineage/*.yaml` 的 `source_tables` + used_by |

---

## 血緣檔（lineage）格式範本

每張 analytic table 一份 YAML：

```yaml
table: <analytic_table>
layer: F2
owner: bi-team
refresh: daily / weekly / monthly
source_tables:
  - raw.<table_1>
  - raw.<table_2>
transformations:
  - name: 欄位重新命名
    detail: raw_col_x → human_col_x
  - name: Join
    detail: raw.a LEFT JOIN raw.b ON ...
  - name: 業務規則
    detail: 排除 test_user, status != 'cancelled'
used_by:
  f3:
    - <datasource_1>
    - <datasource_2>
  f4:
    - <workbook_1>
    - <workbook_2>
```

---

## 擁有者 × 可改 × 通知矩陣

每個箭頭有一行：

| 段 | 擁有者 | 可以改 | 要通知誰 |
|----|--------|--------|---------|
| `raw.*` schema | IT | IT | BI（下游會壞） |
| `raw → analytic` ETL | BI | BI | 業務（指標會變） |
| `analytic` schema | BI | BI | 用到的 workbook owner |
| Datasource SQL | BI | BI | workbook owner |
| Workbook / calc field | workbook owner | workbook owner | 業務 |

**這張表的作用**：
- 任何人要改一欄前，知道該通知誰
- 爭議「這是誰的事」有依據
- 新人上手時知道自己管哪一段

---

## Metrics Dictionary 規範

每個業務指標一條記錄：

```markdown
## 週轉率 (Turnover Rate)

**canonical 定義**：某時段內「車輛被使用的時間」÷「車輛可用時間」

**SQL 範本**：
```sql
SELECT
  city,
  SUM(use_hours) / SUM(available_hours) AS turnover_rate
FROM <analytic_schema>.vehicle_daily
WHERE date BETWEEN ? AND ?
GROUP BY city;
```

**可用時間定義**：... （含維修、保養的扣除規則）
**排除**：test 車輛（`is_test = true`）
**典型用途**：... 、...
**常見混淆**：
- 跟「利用率」不一樣：利用率是 ÷「車輛總數×24h」，不扣可用時間
- 跨期比較要注意：... 的影響
```

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| 血緣只在人腦 | 新人上手要 2 個月 | 寫 yaml 強制外化 |
| 每個 workbook 自己算指標 | 同指標跨 workbook 數字不一 | 強制 metrics dictionary |
| 改欄位沒通知 | 下游 workbook 突然壞 | 擁有者 × 通知矩陣 |
| F3 SQL 散在 Google Sheet | 無版控、無 code review | snapshot 進 git |
| 「這個 table 是幹嘛的」沒人答得出 | schemas 檔無人維護 | 入專案驗收項 |
| Metrics 名稱混用 | 業務說「活躍」，data 說「DAU」，不同東西 | 字典統一命名 |
| 跳 F2 直接做 F3 | 複製邏輯到多個 datasource | 新 analytic table 收斂 |

---

## 檢核清單（建資料 playbook 前對一次）

- [ ] 四層箭頭都定義擁有者了嗎？
- [ ] 每個 analytic table 有 lineage yaml 嗎？
- [ ] 五個核心問答表都有對應位置嗎？
- [ ] Metrics dictionary 建了嗎？
- [ ] SQL cookbook 建了嗎？
- [ ] 擁有者 × 通知矩陣寫了嗎？
- [ ] F3 datasource SQL 有 snapshot 進 git 嗎？
- [ ] 讓新人跑一次：能靠文件自助找到答案嗎？

---

## 相關

- [[funnel-ranking-diagnosis]] — 這個 playbook 的指標字典支援排序診斷
- [[verifiable-judgment-framework-writing]] — 指標定義裡的「判準」照 meta 規則寫

## 真實收益（去識別化）

### 收益 1：新人上手時間下降
原本問資深同事「這欄哪來」要 1-3 天。有 lineage yaml 後，5 分鐘。

### 收益 2：改欄位的衝擊可預估
IT 要改 raw schema 時，BI 可用「反查 lineage」立刻列出受影響 workbook 清單，提前通知。

### 收益 3：AI agent 可用
text-to-SQL agent 讀 metrics dictionary + SQL cookbook，就能回答 60-70% 的 BI 問題，不用人工 handle。
