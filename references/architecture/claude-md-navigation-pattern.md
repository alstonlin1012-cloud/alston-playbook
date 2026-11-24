---
title: CLAUDE.md 導航 pattern — 讓 AI agent 進 repo 的第一站
version: v1
last-updated: 2026-11-10
source: internal bi-pipelines monorepo（去識別化）
---

# CLAUDE.md 導航 pattern

> 大型 monorepo 對 AI agent 最大的阻力不是「code 難懂」，是「不知道該讀哪份細節檔」。這個 pattern 把 repo 根目錄的 `CLAUDE.md` 當作「30 秒速覽 + 常見任務 → 直接跳到哪」的查表入口。agent 進 repo 先讀一份、再翻細節，避免每次 session 都重新搜。

## 情境（什麼時候拿出來用）

- repo 已經累積到「文件 > code 數量」的規模
- 常有新 agent / 新 session / 新同事進來不知道從哪開始
- 細節檔分散在 `docs/`、各 `services/<name>/README.md`、ADR
- 希望「指著一份檔案說：『先讀這份』」就夠了
- 同一 repo 會被多種任務觸發（寫 DAG、建新 service、改部署流程、debug）

## 核心主張

**CLAUDE.md 不是 README 的翻版，是「給 agent 的查表入口」**：

- 人類 README：給人看的 marketing + onboarding
- CLAUDE.md：給 agent 看的**「任務 → 檔案」對照表**
- 兩份都要有、互相引用、內容保持一致

> 關鍵心法：**agent 不會從頭讀完所有文件**。它做什麼要翻什麼，查表比探索快 10 倍。

---

## 骨架（CLAUDE.md 的五個必備段）

### § 1. 這個 repo 是什麼（30 秒速覽）

- 一句話定位
- 頂層目錄＋每個資料夾一行解釋
- 明確標「哪些已 deprecated」（避免 agent 誤觸）

**範例骨架**：
```markdown
## 這個 repo 是什麼

[一句話]。
- `dir1/` — [職責]
- `dir2/` — [職責]（**已 deprecated，見 ADR 00XX**）
- `services/` — 獨立部署的 service，各自 build + deploy
```

### § 2. 設計原則（rebuild 檢核）

一句話概括整個系統的設計目標 + 指向**唯一一份**原則檔。

**鐵則**：原則條文**不要寫在 CLAUDE.md**。CLAUDE.md 只指引「去哪看」。否則原則變更要改兩處，一定不同步。

**範例**：
```markdown
## 設計原則（rebuild 檢核）

[一句話系統目標]。N 條必備原則 + 最新一次現況盤點合放一份：
**[docs/architecture/principles.md](docs/architecture/principles.md)**
——動 code / 設計時對照；若挑戰任一原則，MR description 說明是符合、對齊、還是主動 supersede。
```

### § 3. 常見任務 → 直接跳到哪（核心）

**這是整份文件的 MVP**。表格形式，兩欄：

| user 說什麼 | 你就翻這份 |
|---|---|

**設計要點**：
- 左欄用 **user 語氣的原話**（「flow 改了為什麼 Win host 沒生效」比「同步機制」好）
- 右欄給**具體檔案路徑**＋**一行說明「這份講什麼」**
- 常見任務排前面、冷門排後面
- 跨議題的案例可以引多份（例「先過 A 拿規則，再翻 B 看流程」）

**為什麼 user 語氣**：agent 遇到使用者提問時會做字面比對，`user said: "..."` 的 pattern 匹配比技術詞彙快。

### § 4. 現行方向速覽（timestamped snapshot）

**關鍵段**：寫出「當前 repo 的現況假設」，加日期戳。

**範例**：
```markdown
## 現行方向速覽（2026-07-27）

- **部署機制**：git sync，不是 tarball（ADR 0001 已被 0004 推翻）
- **Flow 路徑注入**：每支 flow 配 `inject.yaml`（committed），由 daemon 內建執行
- **Agent 讀 DAG↔flow 關聯**：靠 docstring 明列，不做自動 asset-map（YAGNI）
```

**為什麼要有這段**：
- ADR 會累積，但「當前走哪條路」容易失焦
- Agent 進來不知道「ADR 00X 是歷史還是當前」
- 這段是**最容易過時**的段，所以**必須有日期戳**

### § 5. 不要做的事（negative space）

明確列 agent 容易踩的 anti-pattern：

**範例**：
```markdown
## 不要做的事

- ❌ **不要動 X 機制** —— 已 deprecated，只給過渡期用
- ❌ **不要在 host 上 `setx` 某 key** —— 會 override `.env`，silent bug
- ❌ **不要合併 A 跟 B 到不同 MR** —— 中間期會指到不存在的資產
- ❌ **不要用 AskUserQuestion 問決策** —— user 明確要 prompt 回，寫在文字讓使用者回覆
```

**為什麼 negative**：
- 「做什麼」agent 會自己推
- 「不要做什麼」agent 猜不到，是過往踩雷的沉澱

---

## 動 code 前的跨題規約（§ 6，選用）

CLAUDE.md 可以放「不限單一任務的規約」，但只放**真正跨議題**的：

| 規約 | 內容 |
|------|------|
| **文件跟 code 一起改** | schema / 命名 / API 變動 → 同 PR 更新對應 doc |
| **跨 repo 動作產 artifact** | 寫到 `docs/cross-repo/`，不直接 push 別人家 repo |
| **Forward-only** | 新資產才放新目錄，舊散檔原地跑直到自然替換 |
| **TODO 格式** | `# TODO(<git user name>, YYYY-MM-DD): <內容>`，方便日後判斷是否過期 |

**鐵則**：單一題目的規約（例：「寫 DAG 的 checklist」）放對應細節檔（`docs/dag-authoring.md`），**不要**塞進 CLAUDE.md。

---

## 跟 README 的分工

| 讀者 | 進來看的 | 檔案 |
|------|---------|------|
| 新同事（人類） | 「這 repo 做什麼、怎麼開始」 | `README.md` |
| AI agent | 「user 說 X，我該翻哪份」 | `CLAUDE.md` |
| 已知任務的 agent / 人 | 具體流程 / checklist | `docs/<topic>.md` |
| 架構決策 | 為什麼選 X 而不是 Y | `docs/decisions/00NN-<slug>.md` |

**兩份頂層文件**（README.md + CLAUDE.md）**應保持一致**：
- 同樣的目錄解釋、同樣的現況假設
- 不同的是「訴求對象」造成的呈現方式
- 其中一份改，另一份要跟著改（放 MR checklist 或 pre-commit hook）

---

## ADR 搭配：forward-only + 推翻可追

CLAUDE.md 不寫「決策歷史」，但要能快速指向 ADR：

**ADR 命名**：`docs/decisions/00NN-<slug>.md`
- `0001-initial-deploy-mechanism.md`
- `0004-git-sync-supersedes-0001.md`（推翻舊決策）

**CLAUDE.md 寫法**：
```markdown
- **部署機制**：git sync（ADR 0001 已被 0004 推翻）
```

**好處**：
- Agent 看到「ADR 0001 已被 0004 推翻」立刻知道哪份是當前
- 歷史決策不失、新人可追
- 推翻的 ADR 不 delete、不改內容、只標 superseded

---

## 跨 repo 交付：artifact 不直 push

當 pipeline 要改別人家 repo，產出 artifact 到自己 repo 的 `docs/cross-repo/`：

```
docs/cross-repo/
├── 2026-07-<target>-schema-change.md    # 給目標 repo owner 的交付單
└── 2026-08-<target>-api-contract.md
```

**artifact 的內容**：
- 目標 repo
- 要改什麼（檔案、函式、版本）
- 為什麼（本 repo 的 context）
- 如何驗證

**為什麼不直 push**：
- 目標 repo 的 owner 有自己的 review 流程
- 直 push 繞過他們的規約是 regression 來源
- artifact 留痕、可 audit

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| CLAUDE.md 寫成 README | 都是描述性文字沒有查表 | § 3「常見任務」是 MVP，不是加分項 |
| 原則條文塞進 CLAUDE.md | 兩份原則檔變更不同步 | § 2 只指引，不寫條文 |
| 現行方向沒日期 | agent 不知道哪些是歷史 | § 4 必有日期戳 |
| 細節檔重複寫規約 | 多份檔案講類似的事 | 單一議題去一個檔，CLAUDE.md 只指引 |
| 「不要做的事」沒寫 | agent 反覆踩同一雷 | § 5 強制存在（過往雷沉澱） |
| CLAUDE.md 太長 | agent 讀完已累 | 控制在螢幕 1-2 頁；長的放細節檔 |
| 跨 repo 直 push | 目標 repo owner 繞過 review | 產 artifact 到 `docs/cross-repo/` |
| 推翻的 ADR 改內容 | 歷史決策追不回 | superseded 標記，不改內容 |

---

## 檢核清單（CLAUDE.md 寫完前對一次）

- [ ] §1「這個 repo 是什麼」30 秒讀完嗎？
- [ ] §2 設計原則指向**唯一一份**原則檔嗎（不重複寫條文）？
- [ ] §3「常見任務 → 直接跳到哪」有表格嗎？用 user 原話寫左欄嗎？
- [ ] §4「現行方向速覽」有日期戳嗎？
- [ ] §5「不要做的事」有嗎？是過往踩雷的沉澱嗎？
- [ ] CLAUDE.md 和 README.md 內容一致嗎？
- [ ] ADR 推翻關係有標 superseded 嗎？
- [ ] 跨 repo 動作走 `docs/cross-repo/` artifact 嗎？
- [ ] TODO 註解格式統一（含 git user name + 日期）嗎？

---

## 完整骨架（可改字複用）

```markdown
# CLAUDE.md — agent 進 repo 的第一站

給任何進來的 AI agent 看的導航。**先讀這份 30 秒，再決定翻哪份細節檔**。
人類版本入口見 [README.md](README.md)；兩份應保持一致。

## 這個 repo 是什麼

[一句話]：
- `[dir]/` — [職責]
- `[dir]/` — [職責]（**已 deprecated，見 ADR 00XX**）

## 設計原則（rebuild 檢核）

[一句話系統目標]。N 條必備原則：**[docs/architecture/principles.md](...)**
——動 code / 設計時對照；若挑戰任一原則，MR description 說明。

## 常見任務 → 直接跳到哪

| user 說什麼 | 你就翻這份 |
|---|---|
| 「[user 原話 1]」 | **[docs/XXX.md](...)** — [一行說明] |
| 「[user 原話 2]」 | [docs/YYY.md](...) — [一行說明] |

## 現行方向速覽（YYYY-MM-DD）

- **[主題 A]**：[當前做法]（ADR 0001 已被 0004 推翻）
- **[主題 B]**：[當前做法]（YAGNI）

## 動 code 前的規約

1. **文件跟 code 一起改**：schema / API 變動同 PR 更新 doc
2. **跨 repo 動作產 artifact**：寫到 `docs/cross-repo/`
3. **Forward-only**：新資產才放新目錄
4. **TODO 格式**：`# TODO(<git user name>, YYYY-MM-DD): <內容>`

## 環境注意

- [runtime 版本]
- [host / 部署目標]
- [認證機制]

## 不要做的事

- ❌ **不要動 X** —— [原因]
- ❌ **不要 Y** —— [原因]
- ❌ **不要 Z** —— [原因]
```

---

## 相關

- [[activity-folder-self-contained-pattern]] — 另一個「給 agent 看」的骨架：業務單元自洽
- [[ai-parallel-first-architecture]] — 整套 AI-first 架構心法，CLAUDE.md 是入口層
- [[bi-knowledge-base-structure]] — 知識庫骨架，CLAUDE.md 的 § 3 查表是其具體化
- [[verifiable-judgment-framework-writing]] — 「不要做的事」本質是一組判準，照 meta 規則寫
