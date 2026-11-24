---
title: 原始碼脫敏流程 — 帶走方法論不帶走機敏，regex + audit report + 不碰原檔
version: v1
last-updated: 2026-11-12
source: internal gsh_data_playbook/07_sanitization_process（去識別化）
---

# 原始碼脫敏流程 methodology

> 離職帶走方法論、建立對外可分享的 playbook、寫公開文件時都會遇到：**原始碼含帳密／內部 domain／私鑰路徑，但業務邏輯（SQL、table 名、欄位、轉換規則）是核心素材必須保留**。這份 methodology 處理「原檔不碰、脫敏副本入版控、可追溯可稽核」三件事——regex 正則替換 + audit report + 版控分層。

## 情境（什麼時候拿出來用）

- 離職要把方法論搬出來，但不能帶公司 raw data / schema / 內部連線
- 要建對外 playbook / 公開文件引用內部實作
- 要給外包商看部分 code 但擋住 credentials
- 工程 ETL script 要進版控但原本 hard-code 帳密
- 這份 alston-playbook 本身就是這個場景的受益者

## 核心主張

**原檔不碰、脫敏副本入版控、兩份 report 留痕**：

1. `input/` 加 .gitignore，脫敏腳本**只讀不寫**
2. `transforms/<type>/` 放脫敏副本，入版控
3. 每次跑產出 `_sanitize_report.json` + `.md`，列哪檔哪行哪類被遮，**不含原值**
4. Idempotent：再跑一次結果相同

**鐵則**：**業務邏輯 100% 保留**，只替換連線細節。SQL、註解、import、業務欄位一律不動。

---

## 骨架（六大設計原則）

| 原則 | 做法 |
|------|------|
| **原檔不碰** | `input/` 加 `.gitignore`，脫敏腳本只讀不寫 |
| **業務邏輯 100% 保留** | 只替換連線細節，不動 SQL / 註解 / import / 業務欄位 |
| **可追溯** | 每檔頂部加 header 標 source 路徑與產出時間 |
| **可稽核** | 產出 report（`_sanitize_report.json` + `.md`）列哪檔哪行哪類被遮，**不含原值** |
| **可重跑** | Idempotent，再跑一次結果相同 |
| **平行映射** | `input/X/Y.py` → `transforms/F2/X/Y.py`，容易追 |

---

## 目錄結構

```
<project>/
├── input/                              # 原始 code（含機敏），.gitignore
│   └── <source-system>/
│       └── <module>/
│           └── <file>.py
├── transforms/
│   └── <type>/                         # 脫敏副本（入版控）
│       ├── <source-system>/
│       │   └── <module>/
│       │       └── <file>.py
│       ├── _sanitize_report.json       # 機器可讀
│       └── _sanitize_report.md         # 人可讀
└── scripts/
    └── sanitize.py                     # 清理腳本
```

**關鍵**：
- `input/` 完全禁止入版控（`.gitignore`）
- `transforms/` 的檔名跟 `input/` 路徑**平行映射**（找得回原檔）
- audit report 兩份都放 `transforms/`，一起 commit（**不含原值**可安全入版）

---

## 替換規則（regex 逐行比對，不走 AST）

**為什麼不走 AST**：簡單夠用。SQL 字串裡出現連線字串的機率極低，實務上 regex 就 cover 99%。

### 典型規則表

| 規則 | 偵測樣式 | Placeholder | 類別 |
|------|---------|-------------|------|
| `upper_var_assign` | `TUNNEL/BASTION/HOST/USER/DB_HOST = "..."` | `<BASTION_HOST>`、`<DB_HOST>` | credential |
| `password_var` | `PASSWORD/DB_PASSWORD/PWD = "..."` | `<DB_PASSWORD>` | credential |
| `secret_call` | `secret('XXX')` | `secret('<SECRET_KEY>')` | credential |
| `ssh_kwarg` | `ssh_username/ssh_password = "..."` | `<SSH_USER>` | credential |
| `ssh_key_path` | `ssh_private_key = "..."` | `<SSH_KEY_PATH>` | credential |
| `pem_literal` | 任何字面值 `"*.pem"` | `<SSH_KEY_PATH>` | credential |
| `user_home_path` | 引號內 `/Users/...` | `<CONFIG_PATH>` | path |
| `internal_domain` | `*.<company>.com` | `<INTERNAL_HOST>` | host |
| `ip_literal` | 字面值 IPv4，**排除** `127.0.0.1`、`0.0.0.0` | `<IP_ADDRESS>` | host |
| `email` | 任何 email 字串 | `<EMAIL>` | pii |

**規則套用順序**：按順序套用，**先命中的優先**。

### 不會被動的（刻意保留）

- **SQL 本體**（`'''...'''`、`"""..."""` 多行字串內的 INSERT/SELECT）
- **Table 名**（`<schema>.<table>`、`public.*`）
- **欄位名、業務 enum 值**
- **DB 名**（例 `goshare_dw`）—— playbook 要知道資料在哪個 DB
- **Port 號、`127.0.0.1`、`0.0.0.0`、`localhost`**
- **Import 區塊、業務註解（`[CHANGE]` 等標記）、重試邏輯**

**鐵則**：不確定是機敏還是業務素材 → **留著**。寧可漏掉一條機敏，也不要把業務邏輯弄殘（因為後者會讓 playbook 失去價值）。

---

## 使用方式

```bash
# dry-run：列出會處理哪些檔，不實際寫出
python3 scripts/sanitize.py --dry-run

# 實跑：讀 input/，寫 transforms/<type>/
python3 scripts/sanitize.py

# 指定不同路徑
python3 scripts/sanitize.py --input other/path --output other/dest
```

**每次原始碼更新後，重跑一次即可**。

---

## Audit Report 設計

**兩份都要產出**：

- `_sanitize_report.json`：機器可讀，含每檔每筆 redaction 的 `{line, rule, category}`
- `_sanitize_report.md`：人可讀，含總表與逐檔明細

**兩份都不含原始值**，只記類別與行號 → commit 入版控 OK。

**為什麼要人可讀版**：
- 稽核時人要看哪些類別被遮多少次
- 新增規則前要先看現在漏掉什麼
- 檢討「是否遮太狠讓業務邏輯失效」

---

## 驗證脫敏完整性

**鐵則**：每次重跑後跑**全文 grep**，確認已知關鍵字無命中：

```bash
grep -rnE "<company_domain>|/Users/<user>|<db_name>|<internal_host>" transforms/
```

有命中 → **補規則、再跑、再驗**。

**第二層偵測**（可選）：
- `detect-secrets` pre-commit hook
- `trufflehog`

---

## 新增規則的流程

```
1. 在 scripts/sanitize.py 的 RULES list 新增 (name, re.compile(...), replacement, category)
2. 若替換需動態邏輯 → 寫對應的 _xxx_sub 函式
3. 重跑 python3 scripts/sanitize.py
4. 全檔抽檢：grep -rnE "<舊關鍵字>" transforms/
```

**為什麼要抽檢**：regex 容易漏邊界 case（換行、escape、多行字串內）。

---

## 已知限制（寫在文件裡避免後人踩）

- **Regex 不懂語法上下文**：若 SQL 字串裡出現 `/Users/...`，會被誤替換。實務上不會發生，但要留意
- **不處理 f-string / `.format()` 動態拼接**（這些本身不含 hard-code 機敏值）
- **不處理非 py 檔**（.ipynb、.yaml、.env 需另外處理）

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| 脫敏腳本動原檔 | 原檔被改壞、沒 backup | 腳本只讀 input/，寫 transforms/ |
| SQL 被誤替換 | 業務邏輯殘 | 連線字串規則只抓變數賦值，不碰字串內容 |
| audit report 含原值 | commit 進版控就外洩 | 只記 `{line, rule, category}` |
| 遮太兇遮到 table / 欄位 | playbook 失去可讀性 | 業務相關字一律保留 |
| 不 idempotent | 再跑結果不一樣 | 設計成冪等 |
| 跑完不驗 | 漏掉某類 | grep 全文驗已知關鍵字 |
| 平行結構沒維持 | 找不回原檔 | `input/X/Y.py` ↔ `transforms/<type>/X/Y.py` |
| localhost 也遮 | code 跑不動 | 排除 `127.0.0.1`、`0.0.0.0`、`localhost` |
| DB 名當機敏遮了 | 讀 playbook 不知道資料在哪 | DB 名保留 |
| 註解一起遮 | 遺失業務背景 | 只遮變數值、字面路徑、字面 domain |
| Import 區塊被動 | import 失效 | Import 一律保留 |

---

## 檢核清單（脫敏跑完前對一次）

- [ ] `input/` 有 `.gitignore`？
- [ ] `transforms/` 的檔名跟 `input/` **平行映射**？
- [ ] 腳本只讀 input 不寫？
- [ ] Audit report 兩份（json + md）都產出？
- [ ] Report **不含原始值**？
- [ ] 業務邏輯（SQL、table、欄位、import、註解）100% 保留？
- [ ] 跑完做 grep 驗證，已知關鍵字無命中？
- [ ] `localhost`、`0.0.0.0`、`127.0.0.1` 排除？
- [ ] Idempotent：再跑一次結果一樣？
- [ ] 「不處理什麼」寫在文件裡（notebooks / yaml / env）？

---

## 相關

- [[verifiable-judgment-framework-writing]] — 脫敏規則本質是判準
- [[handover-doc-skeleton]] — 離職交接文件骨架；這份是 code 層
- [[claude-md-navigation-pattern]] — repo 導航；脫敏跟 CLAUDE.md 一起告訴 agent「原檔在哪、副本在哪」
- [[incident-log-management]] — 漏遮一次 = 一次事件

## 一句話總結

> **帶走方法論不是帶走程式碼原件**。原檔不碰 + regex 替換連線細節 + 業務邏輯 100% 保留 + audit report 留痕—— 讓對外 playbook 既安全又有可讀性，稽核時 commit history 本身就是證據。
