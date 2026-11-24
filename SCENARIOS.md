# SCENARIOS — 按情境反查

> 到了新公司，遇到什麼情境該翻哪幾份。INDEX.md 按產物類型分（methodologies / playbooks ...），這份按**要做的事**分。
>
> 格式：`情境 → 第一順位；第二順位（補強角度）`

最後更新：2026-11-19

---

## 一、分析類

### 做預測（下一季 / 明年銷量、流量、註冊數）
- 開場講給老闆聽 → [預測三命題](templates/forecast-three-propositions.md)
- 實際算 → [多時點 × 多情境預測](frameworks/multi-timepoint-forecast.md)
- 市場天花板 → [人口 × 滲透率拆解](methodologies/population-penetration-decomposition.md) / skill `decomposing-market-decline`

### 業績 / 流量在跌，要診斷
- 排序版（哪家單位先談） → [業績漏斗排序診斷](frameworks/funnel-ranking-diagnosis.md)
- 分類版（哪家是哪種病） → [漏斗失守指紋分群](playbooks/funnel-failure-fingerprint-clustering.md)
- 外部因素（天氣 / 節慶）干擾 → [外生變數歸因還原](methodologies/exogenous-attribution-restoration.md)
- 寫報告 → [業績診斷敘事骨架](templates/business-diagnosis-narrative-skeleton.md)

### 份額 / share 變動分析
- Δpp 拆到產品 + 洞 vs 補血 → [份額變化歸因](playbooks/share-change-attribution.md)

### 市場衰退（長期）
- 母體 vs 行為二層拆 → skill `decomposing-market-decline`

### 單一產品診斷 / EOL 判斷
- 新品崩塌 9 步 + 老品 EOL 四閘 → [單產品診斷 9 步 + EOL 四閘](frameworks/product-diagnostic-nine-step-and-eol-gates.md)

### 業務直覺要驗證 / 老闆丟一個假說
- 通用步驟 → [假設反證法](playbooks/hypothesis-falsification.md)
- 開會現場拆解 + 回會骨架 → [假說檢驗會議紀錄](templates/hypothesis-check-meeting-note.md)

### 要挑戰自己的結論（怕 confirmation bias）
- → [紅隊自我挑戰](methodologies/redteam-self-challenge.md)

---

## 二、工具 / 系統設計類

### 要做 AI 行動建議系統（給第一線用）
- 說服力七要素 → [AI 行動建議系統設計](frameworks/ai-advisory-system-design.md)

### 要做 NL → SQL / BI chatbot
- 分層架構 → [NL → SQL agent 分層](references/architecture/nl-to-sql-agent-layering.md)
- 弱模型 + 程式驗證 → [弱模型 + 確定性驗證](methodologies/weak-model-deterministic-validation.md)

### 要做內部 AI 工具 / 框架
- Framework vs consumer 分工 → [內部 AI 工具框架化 pattern](references/architecture/internal-ai-tool-framework-pattern.md)
- 架構判準（平行跑） → [AI-first 平行開發心法](methodologies/ai-parallel-first-architecture.md)

### 要做多活動 / 多模組 BI app
- 離線 build → JSON → [離線 build → JSON pattern](references/architecture/offline-build-static-json-pattern.md)
- 每場活動自成一夾 → [活動自成一夾 pattern](references/architecture/activity-folder-self-contained-pattern.md)

### 要把散落腳本統一管
- Core + tasks + 三層執行 → [排程任務統一框架 pattern](references/architecture/scheduled-task-unification-pattern.md)

### 大型 repo 要讓 AI agent 好進入
- CLAUDE.md 導航 → [CLAUDE.md 導航 pattern](references/architecture/claude-md-navigation-pattern.md)

### 要給同事 / AI 一個 drop-in skill
- 三個現成範例 → `skills/`（store-handover-impact / validating-replacement-data-sources / decomposing-market-decline）

---

## 三、寫 PRD / 規劃類

### 跟 AI 一起開發（AI 寫 code、人 review）
- 6-phase 骨架 + checkpoint + AI 不能做什麼 → [AI × 人協作 PRD 骨架](templates/ai-human-collaborative-prd-skeleton.md)

### 判準類框架要寫得可驗證
- 9 條元規則 → [可驗證判準框架撰寫法](methodologies/verifiable-judgment-framework-writing.md)
- 舊報告留痕 + NOTE 偏差 → [判準演化追蹤](methodologies/judgment-framework-evolution-tracking.md)

### 紅綠燈 / 健檢儀表板
- 相對同儕 + 帶寬 → [紅綠燈設計 pattern](frameworks/traffic-light-design-pattern.md)

---

## 四、資料 / 稽查類

### 新舊資料源遷移、要對數
- → skill `validating-replacement-data-sources`

### 驗證系統報表準不準（沒有 ground truth）
- 目的性抽樣（刻意選樣） → [目的性抽樣驗證](methodologies/purposive-sampling-for-system-validation.md)

### DB → Google Sheet 自動稽查
- → [DB → Sheet 稽查自動化](playbooks/db-to-sheet-audit-automation.md)

### 要串政府 / 公開 API
- 三層來源 + 坑點 → [政府 API 整合](playbooks/government-api-integration.md)

### 多線並行分析（同資料不同口徑）
- → [多線分析並行管理](playbooks/multi-track-analysis-management.md)

### BI 團隊要建資料流 / 單一事實來源
- → [資料流 playbook F1-F4](templates/data-flow-playbook-skeleton.md)

### 要建 BI 知識庫（人 + AI 共用）
- → [BI 知識庫結構](templates/bi-knowledge-base-structure.md)

---

## 五、團隊 / 管理類

### 3-5 人小團隊要項目管理（不想用 JIRA）
- Sheets + Apps Script + AI → [輕量團隊 tracker](templates/lightweight-team-tracker.md)

### 要建三層管理迴路（主管看 / 經理看 / 第一線看）
- → [三層迴路管理](frameworks/three-layer-management-loop.md)

### 獎金 / 激勵制度要診斷或設計
- 制度 vs 行為、目的別 vs 類別別 → [獎金制度診斷](frameworks/incentive-system-diagnosis.md)

---

## 六、交接 / 傳承類

### 低頻任務要交給下一個人
- 新接手 15 分鐘讀完就會做 → [HANDOVER 骨架](templates/handover-doc-skeleton.md)

### 要給下一個 AI session 繼續寫（不是給新人接手）
- 11 節 context pack → [AI session 交接](templates/ai-session-handoff-doc.md)

### 要把原始碼帶走但不洩漏公司內容
- Regex + audit report + 業務邏輯保留 → [原始碼脫敏流程](methodologies/code-sanitization-for-handover.md)

### 門市 / 分店易主影響評估
- → skill `store-handover-impact`

---

## 七、維運 / 事件類

### 報表半夜壞了要修
- 固定章節 + 症狀跳點 → [報表維運 SOP 骨架](playbooks/report-maintenance-sop-skeleton.md)

### 資安 / 事件 / incident 要追蹤
- 兩態 lifecycle + verdict 對應動作 → [事件簿管理](playbooks/incident-log-management.md)

---

## 八、Meta：找不到時

1. `grep -rE "^title:|^description:" --include="*.md" .` 全撈 frontmatter
2. 到 `alston-playbook/` 目錄 `claude` 直接問：「我要做 X，有哪幾份可以用？」
3. 看 [INDEX.md](INDEX.md)（按產物類型分）
4. 看 [references/source-projects-map.md](references/source-projects-map.md)（按來源專案反查）

---

**共 42 件。情境有重疊，第一順位 = 最直接對應，第二順位 = 補強角度。**
