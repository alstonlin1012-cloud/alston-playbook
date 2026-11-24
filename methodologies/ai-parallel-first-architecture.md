---
title: AI-first 平行開發架構心法 — 用「agent 能不能平行跑」當架構判準
version: v1
last-updated: 2026-11-10
source: internal activity control center refactor（去識別化）
---

# AI-first 平行開發架構心法

> 傳統工程直覺是 DRY（不要重複）、抽共用、追層次優雅。AI-coding-first 專案的最佳化目標不同：**要讓多個 agent 平行改不同模組而不互踩**。重複是 feature、單檔自洽 > 抽象優雅、老模組凍結新模組 copy-paste。這份 methodology 把「反直覺」的那四條排序講清楚，並給出讓它成立的四個契約骨架。

## 情境（什麼時候拿出來用）

- 專案預期要靠多個 AI agent 平行寫、改、驗證
- 專案有「一包一包的獨立業務單元」（活動、campaign、報表、客戶）要重複展開
- 想評估現有架構「是不是 AI-friendly」
- 要給新同事／新 agent 解釋「為什麼我們選擇重複而不抽共用」

## 核心主張

**架構判準不是「這段 code 優不優雅」，而是「這個設計能不能讓 3 個 agent 平行跑而不互踩」**。

答案是否 → 重切。

這跟傳統工程最佳化的目標不一樣：
- 傳統：最小化「程式碼行數／重複度」
- AI-first：最大化「平行開發的安全性＋單檔可理解性」

在 AI-coding 場景，後者價值遠大於前者——因為 agent 一次 `Read` 拿到的 context 是有限的，跨檔依賴 = agent 互踩 = regression。

---

## 四條排序（反直覺）

| 排序 | 原則 | 傳統工程直覺的對立面 |
|---|---|---|
| 1 | **每個業務單元完全自洽** > DRY | 重複是 feature 不是 bug |
| 2 | **單檔可獨立理解** > 抽象優雅 | 寧可一個 `compute.py` 塞 CONFIG+演算法+shape，也不拆 5 個互 import 的小檔 |
| 3 | **任務可拆／可平行／可交叉驗證** > 序列化大改 | 設計時就問「這塊能不能切給 3 個 agent 同時跑」 |
| 4 | **老單元凍結，新單元 copy-paste** > 共用版本管理 | 不為新需求回頭 refactor 老單元 |

### 反模式（看到就擋，即使「程式碼比較漂亮」）

- 抽 `shared_compute/` 給多單元共用 → 違反 §1
- 把 `compute.py` 拆成 `loader.py / algo.py / shape.py` 三檔互 import → 違反 §2
- 改老單元時「順便」refactor → 違反 §4
- 在共用層加「如果是單元 X 就 ⋯」的 if 分支 → 違反 §1 的最糟形式

---

## 分層架構：一條單向資料河

讓四條排序能跑的骨架 — 層與層之間**只靠契約溝通，不靠 import**：

```
原始資料
   │
   ▼  ① 計算層（每個業務單元一份）
   │  <unit>/app/compute.py ← 自洽黑箱
   │    讀資料 → 演算 → 吐 dict（符合資料契約）
   ▼
   │  ② Build 層（薄膠水，整專案共用一份）
   │  掃單元 → 動態 import compute → 蓋 meta/權限 → 輸出 JSON
   ▼
   │  ③ 前端層（無 build step，純函數抽出可單測）
   │  fetch JSON → derive / format / charts 純函數
   ▲
   │  ④ 權限層（雙層 fail-closed）
   │  身分 → 粗粒度 panel 權限 → 進單元後再過細粒度資源權限
```

### ① 計算層 — 自洽黑箱
- **唯一輸入**：`compute(unit_root: Path, today=None) -> dict`
- **內部分區全在單檔**：`CONFIG block(常數) → dataclass 資料模型 → _load_*() → _*_core()/_*_leaderboard() → _*_viewmodel() → compute() 頂層組 JSON`
- **零跨單元依賴**：不 import 別的單元、不抽共用 engine

### ② Build 層 — 薄膠水
只做四件事：
1. 掃 `units/*/`，有 `app/compute.py` 的才撿
2. 動態 `importlib` 載入
3. 呼叫 `compute()` 拿 dict，注入 `meta.permissions`、`generated_at` 等平台欄位
4. 寫成 `<output>/data-<unit_id>.json`

**關鍵**：業務邏輯 100% 在 compute，build 層永遠不為新單元改 code。單元丟進 `units/` 就自動被撿走。

### ③ 前端層 — 無 build step、純函數抽出
- CDN 載框架（Alpine、ECharts 或等價），無 webpack / vite
- 精髓：把「不碰 DOM 的純邏輯」抽成三檔配 `node --test`：
  - `derive.*` — 資料衍生＋權限過濾
  - `format.*` — 格式化／class 決定
  - `charts.*` — 生圖表 option（純配置不碰 DOM）
- 元件層只負責「接 DOM＋呼叫這些純函數」

**為什麼抽純函數**：fixture 好寫、瀏覽器跟 Node 共用一套邏輯、權限過濾集中不散落、效能（display string 一次算好）。

### ④ 權限層 — 雙層 fail-closed
- 第一層（粗）：身分 → 角色 → `allowed_panels`（決定看哪些「頁」）
- 第二層（細）：進單元後比對 `meta.permissions.resources[].visible_to` 決定看哪些「資源」
- 查無身分、角色不在矩陣 → 直接 403，預設拒絕

---

## 四個契約（真正的骨架）

框架能解耦，靠的是「層與層之間用契約溝通」。學會這四個契約就掌握整套：

| 契約 | 定義在哪 | 內容 |
|---|---|---|
| **Compute 介面** | 約定俗成 | `def compute(unit_root: Path, today=None) -> dict`，回傳 `{meta, resources, list, spec}` |
| **資料輸入契約** | `docs/data-contract.md` | 原始資料的欄位、型別、編碼、必填、允許值 |
| **JSON shape 契約** | `docs/data-contract.md §N` | 輸出 JSON 每個 key 的型別與語意 |
| **權限契約** | `config/roles.json` + 單元 `visibility.json` | 角色×panel 矩陣＋資源×角色白名單 |

> 心法：**只要四個契約不變，四層可被不同 agent 平行改。** compute 的人不用懂前端、前端的人不用懂驗證，大家只對著 `data-contract.md`。這份文件就是專案的「API spec」。

---

## SSOT 紀律：spec/README.md 先行

每個業務單元的 `spec/README.md` 是**唯一權威**，跟 code 強制對應：
- §1 單元概要 → `compute.py` 的 CONFIG block
- §2 計算規格 → 演算層 `_*_core()` 函式
- **§3 計算範例（≥ 3 筆具體數字）→ 就是測試對帳基準**
- §4 章節↔函式映射表

**工作流寫死**：先改 spec → 跑通範例 → 才改 compute.py。§3 範例不是文件，是「算對沒」的黃金樣本，也是 baseline snapshot 的依據。

---

## 測試策略：snapshot + 守契約

用三種測試守三件事：
- `test_compute_<unit>.py` → 對 `tests/baselines/<unit>.json` 做 snapshot 比對（算法改了立刻紅）
- `test_permissions.py` → 守權限契約（身分 → role 解析）
- `web/__tests__/*.test.*` → 守前端純函數（改 lib 前先寫 test）

---

## 開新業務單元的標準流程

```
1. cp -r units/<existing-id> units/<new-id>   # 複製範本
2. 寫 spec/README.md                           # SSOT，§3 ≥ 3 筆範例
3. 改 app/compute.py 的 CONFIG block           # 只改常數，不動演算法
4. 寫 visibility.json                          # 每筆資源的 visible_to 白名單
5. tests/test_compute_<unit>.py + baseline     # snapshot 釘住
6. ./build.sh <new-id>  → 看輸出 JSON
7. ./preview.sh         → 本機驗三 tab、數字對得回 spec §3
```

指令刻意拆成獨立入口、各做一件事：
- `./build.sh [id]` — 只 build，不 serve
- `./preview.sh` — build 全部＋起本機 server
- `./deploy.sh` — 只發 image，**不碰線上資料**
- `./daily.*` — prod 資料 pipeline（**開發機別跑會蓋線上**）

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| 新同事看完先想抽共用 | PR 送上來拆了 compute 成三檔 | review 時指 §2，退回 |
| 「反正只多一個單元，先共用一下」 | 半年後 10 個單元共用一個 engine、改不動 | 寧願從一開始重複 |
| 一個單元壞掉牽動其他 | 違反 §1 的徵兆 | 回查看是不是偷偷共用了 |
| 契約沒寫就開工 | 四層各自定義 shape、整合時爆掉 | `data-contract.md` 是 Day 0 工作 |
| spec 跟 compute 對不上 | §3 範例跟實際輸出數字不一致 | 把 §3 當測試 baseline 強制 |
| build 層塞業務邏輯 | 為新單元要改 build layer | 退回業務邏輯到 compute |
| 權限層單層過濾 | 細權限漏判、被看到不該看的資料 | 強制雙層 fail-closed |

---

## 檢核清單（架構 review 時過一遍）

- [ ] 每個業務單元都有獨立資料夾、`compute.py` 自洽嗎？
- [ ] 跨單元有沒有 import？（應該零）
- [ ] 四個契約檔都有嗎（compute 介面、資料輸入、JSON shape、權限）？
- [ ] `spec/README.md` 的 §3 範例是不是測試 baseline？
- [ ] build 層是不是薄膠水（不碰業務邏輯）？
- [ ] 前端純函數抽出來能 `node --test` 嗎？
- [ ] 權限是不是雙層 fail-closed？
- [ ] 新單元流程是不是「cp -r + 改 CONFIG + 跑 build」就夠？
- [ ] 問一次：「這個設計能不能讓 3 個 agent 平行跑而不互踩？」

---

## 相關

- [[activity-folder-self-contained-pattern]] — 本 methodology 的具體落地範本（單元資料夾骨架）
- [[offline-build-static-json-pattern]] — Build 層到前端的靜態 JSON 傳遞方式
- [[nl-to-sql-agent-layering]] — 另一套 AI-first 分工（NL→SQL 三層）

## 一句話總結

> **把「可平行開發」當第一公民，刻意用『重複』換『解耦』，再用四個明確契約把四層黏起來。** 代價是程式碼有重複（每單元一份 compute），但換來改 A 永遠不會炸 B、新人／agent 一次 Read 就懂一個單元。
