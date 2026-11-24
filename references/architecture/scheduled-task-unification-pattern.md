---
title: 排程任務統一框架 pattern — 把散落腳本收進一個 repo，共用 db / env / alert / reporter
version: v1
last-updated: 2026-11-12
source: internal GSH_Automation（去識別化）
---

# 排程任務統一框架 pattern

> BI / Ops 團隊常有一堆散落的排程腳本：每個都自己開 SSH tunnel、讀 config、組 SMTP、寫失敗通知、設 cron。改一個 credential 要翻 10 個 repo。這份 pattern 把分散的排程任務收進一個框架：共用 `core/`、`tasks/` 一檔一任務、三層執行堆疊、統一入口、Mac dev / VM prod 分離。

## 情境（什麼時候拿出來用）

- 團隊有 N 支（≥3）排程腳本，每支都自己處理連線 / 寄信 / 失敗通知
- credential / SMTP / SSH key 改一次要翻好幾個 repo
- 加新任務要抄舊的樣板，容易漏東西
- 想加 `--dry-run` / `--test-email` 統一支援
- 要分 Mac 開發 vs VM 部署、不要混
- 離線環境（無法 pip install）也要跑得了

**跟 [[internal-ai-tool-framework-pattern]] 的差別**：
- 那份：LLM-heavy 工具框架（NL→SQL → Insight）
- 這份：batch-heavy 排程框架（SQL → 格式 → 分發）
- 兩份平行：一個抽象 LLM 管線、一個抽象排程管線

**跟 [[ai-parallel-first-architecture]] 的差別**：
- 那份：AI agent 平行開發的架構心法（compute 自洽、契約驅動）
- 這份：排程任務的執行堆疊 + 共用模組拆法

## 核心主張

**三層分工 + 契約驅動**：

- **Task Scheduler / cron** 只知道「幾點跑哪個任務」
- **PowerShell / bash wrapper** 只處理「切目錄 + venv + exec policy」
- **Python 統一入口** 只處理「load env / log / dispatch / alert」
- **`tasks/<name>.py`** 只寫業務邏輯（SQL / 寄什麼 / 發哪）

**鐵則**：加新 task 只寫 `tasks/<new>.py:run()`，其他層全部不動。

---

## 骨架

### Repo 結構

```
<project>/
├── core/                      # 跨 task 共用模組
│   ├── db.py                  # SSH tunnel + DB connection
│   ├── env_loader.py          # .env loader (OS env 優先)
│   ├── date_utils.py          # 月份區間、民國年轉換等
│   ├── logging_setup.py       # UTF-8 safe logger（修 Windows cp1252 bug）
│   ├── alerts.py              # 失敗通知
│   └── reporters/             # 分發抽象
│       ├── base.py            # Reporter ABC
│       ├── chat.py            # Google Chat / Slack webhook
│       ├── email.py           # SMTP + 附件 + test_mode
│       └── sheet.py           # Google Sheets
├── tasks/                     # 一個檔 = 一個 task
│   ├── <task_a>.py
│   └── <task_b>.py
├── scripts/
│   ├── run_task.py            # 統一入口（Mac/Win 都用這個）
│   └── windows/
│       ├── run_task.ps1       # Task Scheduler wrapper
│       └── deploy.ps1         # VM 一鍵部署
├── wheels/                    # 離線 pip 安裝備援
├── reference/                 # 原始實作（.gitignore，只在本機）
├── tests/                     # pytest
├── .env.example               # 環境變數樣板
├── requirements.txt
└── SPEC.md
```

### Task 契約

每支 task 必須提供：

```python
# tasks/<task_name>.py
TASK_NAME = "<task_name>"

def run(*, dry_run: bool = False, test_email: bool = False, **_) -> None:
    """
    - 失敗直接 raise，不要自己接 alerts（統一入口會處理）
    - --dry-run / --test-email 失敗不觸發通知信（避免 ad-hoc 測試吵到 ops）
    """
    ...
```

**鐵則**：
- 失敗讓 exception propagate，統一入口做 alert
- 不要在 task 內 try/except 呼叫 alerts
- 不要在 task 內載 env / 開 log —— 入口做

---

## 三層執行堆疊（核心）

Task Scheduler / cron 到真正跑 SQL 之間穿過三層，每層只解決一件事：

### 層 1 — Shell wrapper（PowerShell / bash）

**為什麼需要**：
- Task Scheduler 只能啟 `.exe`，不能直接跑 Python
- 要**切到專案目錄**（否則 `import tasks.xxx` 找不到）
- 要**指定用哪個 Python**（系統 Python 沒專案依賴）
- Windows 要 bypass 執行政策

**內容**：
```powershell
Set-Location $PSScriptRoot\..\..
<repo_root>\.venv\Scripts\python.exe scripts\run_task.py $args
```

**對應 Task Scheduler 的 Action**：
```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File <path>\run_task.ps1 <task_name>
```

### 層 2 — `.venv/python.exe`（Python + 隔離環境）

**為什麼 venv 不用系統 Python**：
- 系統 Python 版本未知（2.7 / 3.8 / 3.12），專案要指定版本
- 系統 `site-packages` 混雜各 project 的 package，升一個可能連帶壞別的
- venv = 隔離的小房間，`pip install` 只影響這個 repo

### 層 3 — `scripts/run_task.py`（Python 統一入口）

**流程**：
```python
# 1. 吃 argv
task_name = sys.argv[1]
dry_run = "--dry-run" in sys.argv
test_email = "--test-email" in sys.argv

# 2. 載 .env 塞 os.environ
load_env(".env")

# 3. 開 log
log = setup_logger("run_task", log_dir=os.environ["TASK_LOG_DIR"])

# 4. 動態 import 對應 task
module = importlib.import_module(f"tasks.{task_name}")

# 5. 呼叫它的 run()
try:
    module.run(dry_run=dry_run, test_email=test_email)
except Exception as e:
    log.exception(...)
    if not dry_run and not test_email:
        send_failure_alert(task_name, e)
    sys.exit(1)

sys.exit(0)
```

**Exit codes**：
- `0` 成功
- `1` task 拋例外
- `2` 找不到 task

---

## 分工總表

| 層 | 誰呼叫它 | 解決什麼 | 不做什麼 |
|----|---------|---------|---------|
| `run_task.ps1` | Task Scheduler | 切目錄 + 指定 venv + bypass policy | 不懂業務邏輯 |
| `.venv/python.exe` | PowerShell | 跑 Python + 隔離 package 環境 | 不知道要跑哪支 task |
| `scripts/run_task.py` | Python 直譯器 | 載 env / dispatch / 錯誤處理 / 統一介面 | 不碰 SQL / 寄信 / 具體業務 |
| `tasks/<name>.py` | `run_task.py` | 真正跑 SQL / 寫檔 / 發送 | 不管 schedule / env / alert |

---

## 為什麼不合併

**合併 wrapper + 入口**（讓 shell 直接跑每支 task）→ 每支 task 要自己載 env、處理 exception、發 alert。重複 code。

**合併 入口 + task**（每支 task 都寫完整 `main()`）→ 每加一支 task，`.env` 載入、log 設定、alert 邏輯都要再寫一次。易錯。

**分層 = 每層只負責一件事**。加新 task 時只要寫 `tasks/<new>.py:run()`，其他層全部不動。

---

## 兩環境分離：Mac dev / VM prod

**鐵則**：開發跟部署嚴格分開。

| 環境 | 用途 | 入口 |
|------|------|------|
| **Mac** | 寫 code / 單元測試 / 本地驗 pure 函式 | `python scripts/run_task.py <task> --dry-run` |
| **Windows VM** | 真實 DB 連線 + 排程跑 + 產檔 | Task Scheduler → `run_task.ps1` → `python` |

**兩邊都有 `.env`，但真實 credential 分別維護**（git 都不管）。

---

## 三模式：prod / dry-run / test-email

每支 task 都要支援三種模式：

| 模式 | 旗標 | 行為 |
|------|------|------|
| **prod** | 無 | 真的跑、真的寄 |
| **dry-run** | `--dry-run` | 撈資料但不寄、不寫檔 → 看 SQL 跟輸出是否對 |
| **test-email** | `--test-email` | 寄到測試收件人、subject 加 `[TEST]` → 驗 end-to-end 不吵到正式收件人 |

**鐵則**：`--dry-run` / `--test-email` 失敗 **不觸發通知信**。避免 ad-hoc 測試吵到 ops。

---

## Reporter 抽象（分發統一介面）

```python
# core/reporters/base.py
class Reporter(ABC):
    @abstractmethod
    def send(self, payload: ReporterPayload) -> None: ...

# 具體實作
class ChatReporter(Reporter):     # Google Chat / Slack webhook
    def send(self, payload): ...

class EmailReporter(Reporter):    # SMTP + 附件 + test_mode
    def send(self, payload): ...

class DriveReporter(Reporter):    # Google Drive upload
    def send(self, payload): ...

class SheetReporter(Reporter):    # Google Sheets append
    def send(self, payload): ...
```

**設計要點**：
- 加新分發通道 → 寫新 `Reporter` 子類，task 無感
- `test_mode` 參數讓 EmailReporter 自動切測試收件人、加 `[TEST]` 前綴
- Payload 是 dataclass，欄位固定

---

## 離線 pip 備援（wheels/）

**情境**：VM 網路受限（IRF 審核中、內網隔離），`pip install` 不通。

**解法**：Mac 上 `pip download -r requirements.txt -d wheels/`，把 wheel 一併進 git。

```bash
# VM 上安裝
pip install --no-index --find-links wheels/ -r requirements.txt
```

**鐵則**：wheels/ 是**備援**不是常態。只有在 VM 無網或 pypi 不通時走這條。

---

## `.env` 管理

| 項目 | 做法 |
|------|------|
| **範本** | `.env.example` committed，列所有鍵但值用 placeholder |
| **真實檔** | `.env` 在 `.gitignore`，Mac 跟 VM 各自維護 |
| **讀取** | `env_loader.py` 讀 `.env` 塞 `os.environ`，但 **OS env 優先** |
| **為什麼 OS env 優先** | VM Task Scheduler 可能直接在系統層面設變數，別被 .env 蓋掉 |

---

## 部署：半自動 `deploy.ps1`

**無 CI/CD，全手動**（小團隊 + 低頻排程，不值得 CI）：

```powershell
# 本機跟 VM 之間用 GitLab 或檔案複製
# VM 上執行 deploy.ps1：
#   1. git pull
#   2. 建 .venv（若不存在）
#   3. pip install -r requirements.txt（或 --find-links wheels/）
#   4. schtasks 建/更新排程
#   5. 回報 task 狀態
```

**三個模式**：`FirstTime` / `Update` / `RegisterOnly`。

---

## 慣例（不可違反）

- ❌ **不要把 credential 寫死在 code 裡** —— 全走 `.env` / OS env
- ❌ **不要直接複製 reference/ 裡的舊實作** —— 重構進框架，credential 抽到 `.env`
- ❌ **不要動 `.env` 真實內容** —— 只動 `.env.example` 範本
- ❌ **task 內保留業務邏輯逐字** —— SQL / 收件人 / 訊息模板 / 檔名格式對齊 production
- ❌ **Mac 開發 vs VM 部署嚴格分離** —— Mac 用 Python 入口，VM 走 PowerShell wrapper + Task Scheduler
- ❌ **task 不自己接 alert** —— 失敗 raise 讓統一入口處理

---

## Phase 1 不過度抽象化

**鐵則**：第一輪只要兩支 task 時，**不要為了「以後可能」加抽象層**：
- Reporter 介面 OK（因為真的要 Chat + Email 兩種）
- `tasks/base_task_class.py` 不要（兩支 task 共通點還沒穩）
- 複雜的 config schema 不要（`.env` key-value 夠用）
- Plugin system 不要（加新 task 寫檔就好）

**設計 task 時心裡要有「全任務地圖」但不要先做**。Phase 2/3 加新 task 時發現抽象需要調整，再調。

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| credential 寫死在 code | commit 後外洩 | 全走 `.env` / OS env |
| task 自己接 alert | 失敗處理重複、易錯 | 統一入口接 alert |
| task 自己載 env | 每支要重寫、忘記就 KeyError | 入口統一載 |
| 沒 `--dry-run` | 開發要改 code 才能試跑 | 強制支援 |
| dry-run 失敗觸發 alert | ad-hoc 測試吵 ops | dry-run / test-email 不發 alert |
| wrapper + 入口合併 | 每支 task 處理 env / log | 三層分離 |
| 兩環境混用 | Mac 的 path 進 VM 爆開 | Mac dev / VM prod 嚴格分離 |
| `.env.example` 過時 | 新人少 key | 加 key 時同時改 .example |
| wheels 當常態 | 版本不同步 | 只在 VM 無網時用 |
| Phase 1 就抽象 | 兩支 task 就建 base class | 等第三支出現再抽 |
| commit 到 reference/ | 原始 credential 進版控 | reference/ 必 .gitignore |
| Windows cp1252 中文 bug | log 顯示亂碼 | logging_setup.py 強制 UTF-8 |
| `.env` 在 OS env 之後 | VM Task Scheduler 設的被 .env 蓋 | OS env 優先 |

---

## 檢核清單（建框架前對一次）

- [ ] 三層分工清楚（wrapper / Python / 入口 / task）？
- [ ] Task 契約定下來（TASK_NAME + run(dry_run, test_email, **_)）？
- [ ] 統一入口處理：load env / log / dispatch / alert？
- [ ] 三模式支援（prod / dry-run / test-email）？
- [ ] dry-run / test-email **不觸發** alert？
- [ ] Reporter 抽象（至少 Chat + Email 兩個實作）？
- [ ] `.env.example` 列所有 key？真實 `.env` 在 `.gitignore`？
- [ ] OS env 優先於 `.env`？
- [ ] Mac dev / VM prod 兩套 `.env` 分開？
- [ ] `wheels/` 離線備援（若 VM 無網）？
- [ ] `reference/` 原始 credential 在 `.gitignore`？
- [ ] Phase 1 **不過度抽象**（只做必要共用）？
- [ ] `deploy.ps1` / deploy 腳本三模式（FirstTime / Update / RegisterOnly）？

---

## 相關

- [[internal-ai-tool-framework-pattern]] — 平行的 AI 工具框架化（LLM-heavy）
- [[ai-parallel-first-architecture]] — AI-first 架構心法，task 自洽性對應
- [[claude-md-navigation-pattern]] — 給 agent 進 repo 的導航
- [[incident-log-management]] — 任務失敗處理的事件簿

## 一句話總結

> **散落的排程腳本收進一個框架：core 共用、tasks 一檔一任務、三層執行堆疊、統一入口接 alert、Mac dev / VM prod 嚴格分離**。加新 task 只寫 `tasks/<new>.py:run()`，其他層全部不動。Phase 1 不過度抽象化。
