---
title: 內部 AI 工具框架化 pattern — 框架管管線、consumer 提知識
version: v1
last-updated: 2026-11-10
source: internal bi-ai-framework（去識別化）
---

# 內部 AI 工具框架化 pattern

> 做第一個內部 AI 工具（NL → SQL → 洞察）時整套手寫沒問題。做到第 2、第 3 個時會發現：**90% 是共通管線、10% 是領域知識**。這個 pattern 把共通抽成「核心套件 + 基底映像 + cookiecutter 模板」，讓「做第 N 個工具」變成「寫一份 config + 一份 skill file + 接好資料來源」，而不是整套重寫。

## 情境（什麼時候拿出來用）

- 公司／團隊已經驗證一個 AI 工具的 pattern（例：NL → SQL、NL → 報表、NL → 問答）
- 未來會做多個同類工具（不同領域 / 部門各一）
- 想避免每個工具重寫 FastAPI / guardrails / logging / deploy
- 使用者是「做工具的工程師」，不是「做底層的工程師」
- 要在內部 ecosystem 標準化（限定 cloud、限定 LLM provider、限定 auth）

**跟 [[nl-to-sql-agent-layering]] 的差別**：那份講**單一工具的分工**（翻譯 / 計算 / 寫作三層），這份講**多工具共用骨架的框架化**（怎麼把共通抽出來）。

## 核心主張

**框架負責「管線」，consumer 只提供「知識 + 設定」**。任何特定領域的字串都不該出現在框架核心。

6 層分工：

| 層 | 共通（→ 框架） | 工具特有（→ consumer） |
|---|---|---|
| **Config** | schema、載入、驗證 | `tool.yaml` 的值（project、dataset、allowed tables） |
| **Skill** | skill loader（markdown → 組 context） | `skill/` 下的 markdown（schema / 口徑 / 範例） |
| **NL→SQL** | LLM client、prompt 組裝、retry | skill file 提供的表結構 |
| **Guardrails** | read-only 檢查、allowlist、強制 LIMIT、cost dry-run | allowlist 清單（在 `tool.yaml`） |
| **Executor** | DB client、結果序列化 | 目標 dataset（在 `tool.yaml`） |
| **Insight** | LLM 把結果列摘要 | 摘要語氣／重點（可選，在 skill file） |
| **API** | app factory、`/ask` `/health` `/schema`、auth、logging | 無（直接套用 factory） |

---

## 四個交付物

| # | 交付物 | 作用 |
|---|--------|------|
| 1 | **核心套件**（`<brand>_core`） | 可複用 Python package：config / skills / LLM / NL2SQL / guardrails / executor / insight / FastAPI factory |
| 2 | **基底映像**（`<brand>-base`） | 標準 container：runtime + 核心套件 + 常用 dep |
| 3 | **cookiecutter 模板** | 一鍵長出新工具 repo 骨架 |
| 4 | **共用 CI/CD 範本** | consumer `.gitlab-ci.yml` include 進來即可 |

### Consumer 新工具只要給：
- `tool.yaml`（project / dataset / allowlist / model / skill_dir）
- `skill/` markdown（領域知識 + SQL patterns）
- `app/main.py` 三行（load config → `create_app(config)`）
- 已 sync 到位的資料

---

## Monorepo 結構

```
<brand>-ai-framework/
├── <brand>_core/                  # 可複用核心套件
│   ├── config.py                  # tool.yaml schema + 驗證（pydantic）
│   ├── skills.py                  # skill loader
│   ├── llm.py                     # LLM client（唯一抽象）
│   ├── nl2sql.py                  # NL → SQL
│   ├── guardrails.py              # SQL 安全檢查 + cost dry-run
│   ├── executor.py                # QueryExecutor interface + impl
│   ├── insights.py                # 結果 → 洞察
│   ├── api.py                     # FastAPI app factory + 標準 endpoints
│   ├── logging.py                 # structured logging + audit
│   └── cli.py                     # `<brand>` CLI（init / validate / run / deploy）
├── containers/base/Dockerfile     # 基底映像
├── template/                      # cookiecutter-<brand>-tool
│   └── {{cookiecutter.tool_slug}}/
│       ├── tool.yaml
│       ├── skill/SKILL.md
│       ├── app/main.py            # 套 factory
│       ├── Dockerfile             # FROM <brand>-base
│       └── .gitlab-ci.yml         # include 框架 CI
├── ci/
│   ├── lint.yml / test.yml
│   ├── build-deploy.yml           # consumer 共用
│   └── release.yml                # 版本 tag → 發佈套件 + image
└── docs/
```

---

## MR 序列（怎麼落地的順序）

每個 MR 獨立可 review、可合併。完成一個再開下一個。

### MR-0 — repo scaffold + CI 骨架
- 建 repo + `pyproject.toml`
- 核心模組建空殼 + docstring、import 不報錯
- `.gitlab-ci.yml` 有 lint / test 兩 stage
- README 寫框架用途 + 生態限制

### MR-1 — Config + Skill loader
- `config.py`：pydantic 定義 `ToolConfig`
- `tool.yaml` 載入 + 驗證
- `skills.py`：讀 markdown → 組 system context
- 單元測試：fixture yaml + skill → 正確組出 context

### MR-2 — NL→SQL + Guardrails
- `llm.py`：LLM client（走 ADC、無 API key）
- `nl2sql.py`：prompt 組裝 + `generate_sql()`
- `guardrails.py`：
  - 🔴 拒絕 DML / DDL（INSERT / UPDATE / DELETE / DROP / ALTER / MERGE / TRUNCATE）
  - 🔴 只允許 `allowed_tables`
  - 🟡 無 LIMIT 自動補 `default_row_limit`
  - 🟡 multi-statement 拒絕
- cost dry-run：估 bytes 超標直接擋
- 失敗回結構化錯誤（reason code）不只 raise

### MR-3 — Executor + Insight
- `executor.py`：`QueryExecutor` interface + 預設 impl
- 結果序列化成 `list[dict]` + schema metadata
- `insights.py`：`summarize()`；rows 過多先抽樣再餵
- 整合測試（可用 public dataset）

### MR-4 — FastAPI factory + 標準 endpoints
- `api.py`：`create_app(config) -> FastAPI`
- `POST /ask`：`{question}` → `{sql, rows, insight, cost_bytes, reason_code?}`
- `GET /health`：build version + config 摘要（不含 secret）
- `GET /schema`：allowlist 表 + skill 摘要
- `logging.py`：每次 /ask 一筆 structured log

### MR-5 — Container 部署 + 完整 CI/CD
- 基準路徑：`gcloud run deploy --source .`（不需預建 base image 即可上線）
- 最佳化：base image 加速 consumer build（基準有痛點再導）
- CI：validate → build → 漏洞掃描 → deploy
- Deploy auth：**最小權限 SA key**（masked + protected CI variable、排程輪替）
- staging / prod 分開，prod `when: manual`

### MR-6 — Cookiecutter 模板 + dogfooding 遷移
- `<brand> init <slug>` 長出可跑的 repo 骨架
- 模板含：`tool.yaml` 範例、`skill/SKILL.md` 骨架、`app/main.py`、`.gitlab-ci.yml`、README
- 把**第一個驗證過的工具遷移到框架上**（dogfooding）
- 遷移後既有功能行為不變（用幾題既有 query 回歸）

### MR-7 — 稽核 / 限流 / Eval 收斂
- **query 稽核**：每次 /ask 一筆 log 到 DB（`audit_enabled` / `audit_dataset` 開關）
- **速率限制**：每使用者每分鐘上限（`rate_limit_per_min`）
- **Eval 題庫**：`eval/cases.yaml` + `compare_rows`
- 澄清 / 圖表 / 多輪 history（dogfooding 發現的 gap）

---

## CI/CD 設計

### 框架 repo 的 pipeline
```
lint → test → build-base-image → release(套件+image)
```

- `build-base-image`：merge main 後 build 基底映像 push registry，tag = commit short SHA
- `release`：git tag `vX.Y.Z` 觸發 → 發佈 package 到私有 registry + 推 image

### Consumer repo 的 pipeline

```yaml
# consumer 的 .gitlab-ci.yml
include:
  - project: '<org>/<brand>-ai-framework'
    file: '/ci/build-deploy.yml'
    ref: v0.1.0          # 固定版本，框架升版不會偷偷影響工具
```

- Consumer 只跑 `validate(tool.yaml + skill)` → build → deploy，不重跑核心測試
- Consumer 在 `pyproject.toml` pin `<brand>-core==X.Y.Z`，**明確升版**才吃到框架改動

### 版本控制原則
- **Semantic Versioning**：breaking change 升 major
- 框架 API（`create_app`、`tool.yaml` schema）視為**公開契約**
- 🔴 **不允許**「改框架核心去 patch 單一工具的問題」—— 工具特有問題進 consumer repo

---

## 安全紅線（五條）

| 等級 | 原則 |
|------|------|
| 🔴 | **零 hard-code 憑證**。走 Secret Manager + ADC |
| 🔴 | **SQL 唯讀**。guardrails 是必經之路，繞過 guardrails = review 直接擋 |
| 🔴 | **Table allowlist**。LLM 只碰 `tool.yaml` 列出的表 |
| 🟡 | **Cost ceiling**。每次查詢有 `max_bytes_billed`，避免 LLM 生出全表掃描燒錢 |
| 🟡 | **存取控制**。cloud service 走 IAP / SSO，授權名單走**中央權限樹**，不手動逐個綁 email |

---

## Non-Goals（避免 scope creep）

明確列「這份框架**不**做什麼」：

- ❌ 不做通用 RAG / 向量檢索 —— skill file 是靜態 markdown，由 LLM 長 context 載入
- ❌ 不做多 warehouse 完整實作 —— v1 只做 BQ，interface 乾淨保留未來加 PostgreSQL
- ❌ 不做多 LLM provider 抽象 —— 內部生態只用一家，不為「彈性」加其他 provider
- ❌ 不把單一工具的業務邏輯塞進框架 —— 業務邏輯一律放 consumer skill file

**為什麼**：框架生態限制越少 → 框架越複雜 → consumer 越難用。

---

## 已知風險（SemVer × 抽象驗證）

| 等級 | 風險 | 緩解 |
|------|------|------|
| 🔴 | 部署 SA key 洩漏面 | 最小權限 + masked + protected + 排程輪替 + 中長期推 WIF |
| 🟡 | Skill context 超 LLM token 上限 | 先記 TODO，視情況做 skill 分段/聚焦載入 |
| 🟡 | 框架 API 改動破壞 consumer | SemVer + 公開契約凍結 + CHANGELOG migration note |
| 🟡 | LLM 產出 SQL 正確但口徑錯 | 框架只保證「能跑、安全」，不保證「業務正確」。正確性靠 consumer skill + 回歸題庫 |
| 🟡 | **僅一個 consumer 驗證（premature abstraction）** | 盡早確認下一個工具的形狀 sanity-check 公開契約，**確認後再凍結**（先別發 v1.0.0） |
| ⚪ | 多 warehouse 需求 | executor interface 保留 |
| ⚪ | 模板跟框架版本漂移 | release 時一併更新模板 ref |

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| 一開始就抽框架 | 第一個工具還沒做完就想泛化 | 先做完驗證、再抽第二個 |
| 僅一個 consumer 就凍結 v1.0 | premature abstraction、改不動 | 等第二個 consumer sanity-check 後再凍結 |
| 塞特定領域邏輯進核心 | 「GoShare 的某欄位寫死」 | 搬進 consumer skill |
| Consumer 也重跑核心測試 | CI 時間翻倍 | consumer CI 只 validate + build + deploy |
| 框架改核心去 patch 工具 bug | 工具專屬 bug 污染框架 | 工具 bug 進 consumer repo |
| 允許繞 guardrails | 緊急情況「暫時」繞過 → regression | guardrails 是必經之路，不可繞 |
| hard-code 憑證 | 老工具的技術債延續 | 零 hard-code、全 ADC |
| LLM 可碰所有 dataset | 問到不該問的 | allowlist 強制 |
| 沒 cost ceiling | LLM 生出全表掃描燒錢 | `max_bytes_billed` 必設 |
| 沒 audit log | 問題事後查不到 | 每次 /ask 一筆 structured log |

---

## 檢核清單（抽框架前對一次）

- [ ] 至少一個工具已實作過（不是紙上抽象）？
- [ ] 分層表（共通 vs 工具特有）列清楚了嗎？
- [ ] 四交付物（核心套件 / 基底映像 / 模板 / CI 範本）都定義了嗎？
- [ ] MR 序列拆得夠細（每個 MR 可獨立 review / merge）嗎？
- [ ] 公開契約（API + yaml schema）清楚嗎？
- [ ] SemVer + migration note 制度建好了嗎？
- [ ] 安全紅線五條（零憑證 / 唯讀 / allowlist / cost ceiling / 中央權限樹）都落實？
- [ ] Non-Goals 寫清楚了嗎？
- [ ] 是否已有第二個 consumer 可以 sanity-check？（沒有就先別凍結 v1.0）
- [ ] Dogfooding：第一個工具遷移到框架上，行為不變？

---

## 相關

- [[nl-to-sql-agent-layering]] — 單一工具的分工（翻譯 / 計算 / 寫作三層）
- [[ai-parallel-first-architecture]] — AI-first 架構心法；框架也是 agent 跑的環境
- [[claude-md-navigation-pattern]] — 框架 repo 的 CLAUDE.md 入口設計
- [[verifiable-judgment-framework-writing]] — guardrails 的判準本身照 meta 規則寫

## 一句話總結

> **把第一個工具做對，第二個工具抽框架，第三個工具驗證抽象**。框架負責管線、consumer 提知識；共通進核心、特有留 yaml / skill。凍結公開契約前先等第二個 consumer 幫你 sanity-check。
