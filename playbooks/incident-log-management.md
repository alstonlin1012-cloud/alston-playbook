---
title: 事件簿管理 playbook — 從 CVE 處理抽象出的 incident log 通用原則
version: v1
last-updated: 2026-11-10
source: internal bi-security-scan（去識別化）
---

# 事件簿（incident log）管理 playbook

> 從處理 CVE 事件的實作過程中萃取出的**跨事件通用**原則。CVE 只是觸發場景——同樣的骨架適用於資料事件、合規事件、客訴事件、SLA 違規、任何「有一堆待處理項、要追蹤到結案、未來要能回頭查」的工作。

## 情境（什麼時候拿出來用）

- 要建立一套「事件管理」的常態機制（不是一次性救火）
- 多個 host／repo／部署端要逐一處理到 all green
- 需要「處理前 vs 處理後」證據留痕
- 要避免「事件懸在 50%」狀態（下次打開不知道差什麼）
- 要讓外部條件（等 upstream、等 vendor）的事件不被遺忘

## 核心主張

**事件簿不是文件，是「狀態機 + 證據留痕」**：

1. **狀態只有兩態**：進行中 / 已結案（YYYY-MM-DD）。沒有「50% 完成」、「已處理待驗證」等中間態。
2. **每個 non-clean finding 都要有結論**。要嘛處理完、要嘛「不處理 + 理由」、要嘛「等 X」。
3. **掃描覆蓋要跟 README 覆蓋範圍對齊**。悄悄縮水範圍 = 假的 clean。
4. **驗證三層分開**：host / repo / 部署端。改 repo 不會自動更新 host，更不會自動更新部署。

---

## 骨架（事件 lifecycle）

### 階段 1 — 開事件（triage）

每個事件開寫時立刻列出：

- **狀態**：`進行中` 或 `進行中（等外部：<條件>）`
- **全部影響面**：先在 README 列完全部範圍（即使暫時不掃）
- **掃描覆蓋**：決定要覆蓋哪些、哪些不掃（連「不掃的理由」一起寫）
- **結案條件**：**可機械驗證**的清單（例「scan `--only vulnerable` 回空」比「所有洞修完」好）

> **鐵則**：全部影響面 ≠ 掃描覆蓋。差異寫進 README 的「不掃」註記。

### 階段 2 — 掃描（verdict → 動作對應）

每個 finding 必有 verdict，每個 verdict 對應明確動作：

| verdict | 使用者該做 | 符號 |
|---------|-----------|-----|
| `vulnerable` | **修**，直到變 clean | ❌ |
| `conditional` | **確認**版本是否其實已 patched，or 判定「不處理 + 理由」寫進 remediation | ⚠️ |
| `unknown` | **補判準 / 補掃描範圍**，或人工驗證後寫結論 | ❓ |
| `manual` | **人工檢查**，結果寫進 remediation（「已確認 X，clean」/「不用，無部署」） | ⓘ |
| `clean` | 無事 | ✅ |

**關鍵設計**：
- `manual` 是 **first-class verdict**，不是「省略」。刻意不自動化判斷的項目，用 `manual` 明示給使用者看
- `manual` **不觸發 exit code 1**（不擋 CI gate），只是提醒
- 悄悄省略 → 使用者看到 clean 以為全掃過 → 「假的 clean」

### 階段 3 — 處理（三層分開）

Blast radius 永遠分三層評估、分三層處理：

| 層 | 問題在哪 | 處理方式 | 驗證證據 |
|----|---------|---------|---------|
| **host** | 開發機 runtime 版本 | 升本機工具（nvm / brew / apt） | host scan 回 clean |
| **repo** | 原始碼內的版本宣告 | 改 Dockerfile / CI yaml / 版本 pin 檔 | repo scan 回 clean |
| **deploy** | 實際線上跑的版本 | **要 rebuild + redeploy**（改 repo 不會自動 propagate） | 部署端 revision 使用新 image |

**Why**：三層獨立。改 repo 不會自動更新 host（dev 要自己升），更不會自動更新 deploy（要 push + CI/CD trigger 重 build + redeploy）。

**How to apply**：
- remediation.md 的「處理方式」節**逐層列**，不要混在一起
- 事件結案前，**三層都要有驗證證據**

### 階段 4 — 一次 remediation 包三件：改檔 + 掃描 + 快照

```
改檔 → 重跑 scan → --save-reports 存快照
```

缺一不可：
- 只改檔不掃 → 不知道有沒有漏
- 只掃不存 → 下次對不出 before/after
- 存快照方便 remediation.md 引用「處理前 / 處理後」的證據

事件結案前，`reports/` 內一定有至少兩份：
- **處理前 vulnerable 快照**
- **處理後 clean 快照**

JSON 快照直接 git commit 進 repo，事件簿就是 incident log。

### 階段 5 — 結案條件（all 都滿足才能結案）

1. 所有 scan `--only vulnerable` 回空
2. 所有 `conditional` / `unknown` 的 finding 都在 remediation.md 有「處理完 / 等 X / 不處理 + 理由」結論
3. 所有 `manual` 都在 remediation.md 標記「已確認（含版本證據）」或「不處理 + 理由」
4. 所有 repo 的 patch 都 push + 部署端 revision 跑新版

> **鐵則**：不要為了「看起來乾淨」就提前結案。事件簿要如實反映現狀。

---

## 外部條件過渡態（最容易漏的 pattern）

等 upstream patch、等 vendor advisory、等其他 team 回應——事件 **仍然 open**。

**狀態寫法**：`進行中（等外部：apache/arrow#55166 patch）`

**How to apply**：
- 保留 open 狀態 = 強制定期回頭看
- **週期掃描**（例如每月初）掃一輪所有「進行中」事件，看外部條件是否達成
- 外部條件達成 → 立即接手推進剩下步驟
- 「等外部」是正常過渡態**不是**結案理由

**Why**：等外部的事件若悄悄被遺忘，是最大 regression 來源。

---

## 事件簿檔案結構（建議）

```
events/
├── README.md                  # 事件簿總表、命名規則、workflow
├── PRINCIPLES.md              # 本 playbook 的具體化版（跨事件通用原則）
└── <YYYY>-<topic>-<id>/
    ├── README.md              # 事件本身：狀態、覆蓋範圍、結案條件
    ├── remediation.md         # 處理紀錄（逐層、逐項、附時間戳）
    └── reports/
        ├── <timestamp>-before.json   # 處理前快照
        └── <timestamp>-after.json    # 處理後快照
```

**README.md** 必有段落：
1. 狀態 + 結案條件清單
2. 覆蓋範圍（全部影響面）
3. 掃描方式（含「不掃 X / Y，原因 Z」）
4. 攻擊／影響可達成的範圍（3-5 列即可，不寫 exploit 細節）

**remediation.md** 每筆 non-clean finding：
- 時間戳
- 處理方式（host / repo / deploy 三層）
- 證據（scan output or 其他 verification）

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| 省略不自動化的項目 | scan 回 clean，但其實沒掃某類 | 用 `manual` verdict 明示 |
| 事件 50% 結案 | 下次打開不知道差什麼 | 強制兩態：進行中 / 結案 |
| 改 repo 就當好了 | 線上 image 還跑舊版 | 三層驗證都要 |
| scan 回綠就改 scan 判準 | 看似結案其實作弊 | 快照放 reports/，不改判準 |
| 不留快照 | 對不出 before/after | 結案前兩份快照強制 |
| 外部條件 → 直接結案 | 事件消失、regression | 保留 open + 定期掃 |
| manual 一直懸著 | 事件簿變廢紙 | 升級為 vulnerable 處理掉，或寫「已 ack 不處理」 |
| 「我們不用」= 不掃 | 新機器進來爆開 | 把「不用」寫 remediation，不要當 silent skip |

---

## verdict 判斷流程（圖）

```
掃到一個 finding
       │
       ▼
   有自動判準嗎？
       │
   ┌───┴───┐
  No      Yes
   │       │
   ▼       ▼
`manual`  自動 verdict
   │     （vulnerable / conditional / unknown / clean）
   │       │
   └───┬───┘
       ▼
   寫進 remediation.md
       │
   ┌───┴───┐
   │       │
 處理後    決定不處理
   │       │
   ▼       ▼
再掃一次  寫理由、ack
   │       │
   └───┬───┘
       ▼
    結案條件都滿足？
       │
   ┌───┴───┐
  No      Yes
   │       │
   ▼       ▼
 進行中   已結案(YYYY-MM-DD)
```

---

## 檢核清單（事件結案前對一次）

- [ ] 狀態是「進行中」或「已結案(YYYY-MM-DD)」，沒有中間態？
- [ ] scan `--only vulnerable` 回空？
- [ ] 每個 `conditional` / `unknown` / `manual` 在 remediation.md 有結論？
- [ ] 處理前、處理後各有一份快照存在 reports/？
- [ ] 三層（host / repo / deploy）都有驗證證據？
- [ ] 覆蓋範圍 vs 掃描範圍差異寫在 README 的「不掃」段？
- [ ] 攻擊／影響範圍段 3-5 列寫清楚了？
- [ ] 外部條件（等 upstream / vendor）標記在狀態裡？

---

## 相關

- [[verifiable-judgment-framework-writing]] — verdict → 動作對應表本身是一組判準，照 meta 規則寫
- [[hypothesis-falsification]] — 「這個 finding 其實是 vulnerable 嗎」要用假設反證驗證
- [[db-to-sheet-audit-automation]] — 類似的「狀態機 + 證據留痕」思路應用在資料稽查

## 延伸應用（不止 security）

這套骨架可以直接套在：

| 場景 | 「事件」 | verdict 對應 | 結案條件 |
|------|---------|-------------|---------|
| **資料品質** | 一個失敗的對帳 check | pass / mismatch / needs-manual | 所有 mismatch 有處理紀錄 |
| **SLA 違規** | 一次 downtime | need-postmortem / resolved / wont-fix | 跟 oncall + 使用者對齊 |
| **客訴** | 一張 ticket | new / replied / resolved | 回覆 + 使用者確認 |
| **合規** | 一項稽核缺失 | gap / patched / accepted-risk | 補件或風險允收決議 |
| **資料源遷移** | 新舊欄位對不上 | match / drift / manual-mapping | 每筆 drift 有對應 mapping |

**共同點**：有狀態、有 verdict、有「不處理 + 理由」是合法終態、有外部條件過渡態、要留痕。
