# INDEX — 全框架索引

> 格式：`- [標題](path) — 一句定位 · 狀態`
>
> 按**情境**反查：見 [SCENARIOS.md](SCENARIOS.md)（新公司會遇到的事 → 翻哪幾份）
> 按**來源**反查：見 [references/source-projects-map.md](references/source-projects-map.md)

最後更新：2026-11-19

---

## 分析方法論（methodologies/）

- [假設反證法 (hypothesis-falsification)](playbooks/hypothesis-falsification.md) — 業務直覺假設拿到數據證偽通用步驟 · ✅ v1
- [可驗證判準框架撰寫法](methodologies/verifiable-judgment-framework-writing.md) — 任何判準框架 9 條元規則 · ✅ v1
- [外生變數歸因還原法](methodologies/exogenous-attribution-restoration.md) — 固定效應迴歸剝離天氣／節慶／外部事件 · ✅ v1
- [人口 × 滲透率拆解法](methodologies/population-penetration-decomposition.md) — 把衰退拆成「母體變化」vs「行為變化」 · ✅ v1
- [AI-first 平行開發架構心法](methodologies/ai-parallel-first-architecture.md) — 用「agent 能不能平行跑」當架構判準 · ✅ v1
- [弱模型 + 確定性驗證](methodologies/weak-model-deterministic-validation.md) — 不要求 LLM 聰明，要求講得清楚，對不對交給程式判 · ✅ v1
- [目的性抽樣驗證系統報表](methodologies/purposive-sampling-for-system-validation.md) — 不是隨機抽樣，是刻意選樣讓每種失效情境都被看到 · ✅ v1
- [判準演化追蹤](methodologies/judgment-framework-evolution-tracking.md) — 舊報告是修正前的樣子，留著 + NOTE 偏差標記，規則才有血肉 · ✅ v1
- [紅隊自我挑戰](methodologies/redteam-self-challenge.md) — 派兩個 subagent 打自己論點、四級分類、產收回/改口表 · ✅ v1
- [原始碼脫敏流程](methodologies/code-sanitization-for-handover.md) — 帶走方法論不帶機敏：原檔不碰 + regex 替換 + audit report + 業務邏輯 100% 保留 · ✅ v1
- 市場衰退二層拆解（母體 vs 行為） — skill `decomposing-market-decline` · ✅

## 診斷框架（frameworks/）

- [業績漏斗排序診斷](frameworks/funnel-ranking-diagnosis.md) — 把 N 家單位指標收斂成一個排序問題 · ✅ v1
- [三層迴路管理](frameworks/three-layer-management-loop.md) — 從被動 dashboard 到主動派單系統 · ✅ v1
- [單產品診斷 9 步漏斗 + EOL 四閘門](frameworks/product-diagnostic-nine-step-and-eol-gates.md) — 新品崩塌診斷 / 老品 EOL 判準 · ✅ v1
- [獎金 / 激勵制度診斷](frameworks/incentive-system-diagnosis.md) — 制度 vs 行為、目的別 vs 類別別 · ✅ v1
- [紅綠燈設計 pattern](frameworks/traffic-light-design-pattern.md) — 一眼可讀的健檢：相對同儕 + 帶寬 · ✅ v1
- [AI 行動建議系統設計](frameworks/ai-advisory-system-design.md) — 說服力七要素、寧可少建議不可弱建議 · ✅ v1
- [多時點 × 多情境預測框架](frameworks/multi-timepoint-forecast.md) — 資料可得性決定方法：月初 MoM、月中/底 base × bump · ✅ v1
- 門市 handover 影響判準框架 — skill `store-handover-impact`（已 skill 化、已複製） · ✅
- 新舊資料源遷移驗證框架 — skill `validating-replacement-data-sources` · ✅

## 執行 Playbooks（playbooks/）

- [假設反證法通用版](playbooks/hypothesis-falsification.md) — ✅ v1
- [多線分析並行管理](playbooks/multi-track-analysis-management.md) — 同輸入多口徑、改一處連動多處 · ✅ v1
- [政府／機關開放資料整合](playbooks/government-api-integration.md) — 三層來源盤點 + 坑點清單 · ✅ v1
- [DB → Google Sheet 稽查自動化](playbooks/db-to-sheet-audit-automation.md) — 主管機關稽查 SOP · ✅ v1
- [事件簿管理](playbooks/incident-log-management.md) — incident log 通用原則：兩態 lifecycle、verdict 對應動作、三層驗證 · ✅ v1
- [報表維運 SOP 骨架](playbooks/report-maintenance-sop-skeleton.md) — 固定章節 + 症狀跳點 + 可 copy 指令，半夜 oncall 照做 · ✅ v1
- [份額變化歸因](playbooks/share-change-attribution.md) — 品牌 share Δpp 拆到車款、洞 vs 補血、五類型判可持續 · ✅ v1
- [漏斗失守指紋分群](playbooks/funnel-failure-fingerprint-clustering.md) — k-means 分不出來時改用最上游失守點指派主群 · ✅ v1

## Claude Skills（skills/）

- `store-handover-impact` — 門市易主影響分析 · ✅ 已複製（使用者授權保留真實名稱、剝除內部連結）
- `validating-replacement-data-sources` — 新舊資料源遷移驗證 · ✅ 已複製（零洩漏）
- `decomposing-market-decline` — 市場衰退二層拆解 · ✅ 已複製（零洩漏）

## 模板（templates/）

- [預測類專案開場白三命題模板](templates/forecast-three-propositions.md) — 「量不是重點，需求結構才是」 · ✅ v1
- [資料流 playbook 骨架 F1-F4](templates/data-flow-playbook-skeleton.md) — BI 團隊 single source of truth · ✅ v1
- [BI 知識庫結構](templates/bi-knowledge-base-structure.md) — 人 × AI agent 共用知識庫設計 · ✅ v1
- [業績診斷敘事骨架](templates/business-diagnosis-narrative-skeleton.md) — 發生 → 為什麼 → 是誰 → 做什麼 → 邊界 · ✅ v1
- [HANDOVER 骨架](templates/handover-doc-skeleton.md) — 低頻任務交接入口文件：新接手 15 分鐘讀完就會做 · ✅ v1
- [輕量團隊 tracker](templates/lightweight-team-tracker.md) — 3-5 人團隊 Google Sheets + Apps Script + AI 取代 JIRA · ✅ v1
- [AI × 人協作 PRD 骨架](templates/ai-human-collaborative-prd-skeleton.md) — 每 phase 明示誰做、哪裡 checkpoint、AI 不能做什麼 · ✅ v1
- [假說檢驗會議紀錄](templates/hypothesis-check-meeting-note.md) — 老闆提的合理假說，拆可檢驗推論 + 關鍵反證 + 資料缺口 · ✅ v1
- [AI session 交接文件](templates/ai-session-handoff-doc.md) — 給下個 session 繼續寫（不是給新人接手）：11 節 context pack · ✅ v1

## 系統 / 架構 pattern（references/architecture/）

- [離線 build → JSON → 前端純讀 pattern](references/architecture/offline-build-static-json-pattern.md) — 多活動 BI app 的輕量架構 · ✅ v1
- [每場活動自成一夾 pattern](references/architecture/activity-folder-self-contained-pattern.md) — 反 engine 的組織方式 · ✅ v1
- [NL → SQL → LLM 解釋 agent 分層](references/architecture/nl-to-sql-agent-layering.md) — 翻譯 / 計算 / 寫作分工 · ✅ v1
- [CLAUDE.md 導航 pattern](references/architecture/claude-md-navigation-pattern.md) — 大型 repo 讓 agent 進來的第一站：常見任務 → 直接跳到哪 · ✅ v1
- [內部 AI 工具框架化 pattern](references/architecture/internal-ai-tool-framework-pattern.md) — 框架管管線、consumer 提知識；6 層分工 + MR 序列 + 公開契約凍結時機 · ✅ v1
- [排程任務統一框架 pattern](references/architecture/scheduled-task-unification-pattern.md) — 散落腳本收進一個 repo：core 共用 + tasks 一檔一任務 + 三層執行堆疊 · ✅ v1

---

## 進度（截至 2026-11-19）

- ✅ 完成：42 件 — 五輪 35 件 + Pass 1 兩批 5 件 + Pass 2 近週新增 2 件
  - **Pass 2（2026-11-19，兩件）** — 近一週使用者新做的專案：
    - `references/architecture/scheduled-task-unification-pattern.md` — 從 GSH_Automation 抽
    - `templates/ai-session-handoff-doc.md` — 從 bi-knowledge-base/_working/playbook-plan 抽
  - **Pass 1 批次 2（2026-11-12，兩件）**：
    - `methodologies/code-sanitization-for-handover.md` — 從 gsh_data_playbook/07_sanitization_process 抽
    - `playbooks/funnel-failure-fingerprint-clustering.md` — 從 rs_sales_track/門市分群與輔導方案 抽
  - **Pass 1 批次 1（2026-11-11，三件）**：
    - `methodologies/judgment-framework-evolution-tracking.md` — 從 tainan_ms%_yongkang_change NOTE 抽
    - `methodologies/redteam-self-challenge.md` — 從 market_info/strategy/redteam_findings 抽
    - `templates/hypothesis-check-meeting-note.md` — 從 rs_sales_track/會議紀錄 抽
  - **第五輪新增（2026-11-11，一件）**：
    - `templates/ai-human-collaborative-prd-skeleton.md` — 從 app_video 抽
  - **第四輪新增（2026-11-11，三件）**：
    - `methodologies/purposive-sampling-for-system-validation.md` — 從 cctv 抽
    - `methodologies/weak-model-deterministic-validation.md` — 從 sales_pulse_training 抽
    - `templates/lightweight-team-tracker.md` — 從 bi_team_tracker 抽
  - **第三輪新增（2026-11-11，兩件）**：
    - `templates/handover-doc-skeleton.md` — 從 sales_review/HANDOVER 抽
    - `playbooks/share-change-attribution.md` — 從 2026_reg_forecast 抽
  - **第二輪新增（2026-11-10，六件）**：
    - `methodologies/ai-parallel-first-architecture.md` — 從 richard_handover 抽
    - `playbooks/incident-log-management.md` — 從 bi-security-scan 抽
    - `playbooks/report-maintenance-sop-skeleton.md` — 從 key_report_sop 抽
    - `frameworks/multi-timepoint-forecast.md` — 從 mvo_forecast 抽
    - `references/architecture/claude-md-navigation-pattern.md` — 從 bi-pipelines 抽
    - `references/architecture/internal-ai-tool-framework-pattern.md` — 從 bi-ai-framework 抽
  - **第一輪 23 件**：見 2026-11-04 盤點清單
- ⏳ 待抽：無（候選已全部收完或判定低可攜性）
