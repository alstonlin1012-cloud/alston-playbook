# 來源專案對照表

每份 playbook / framework / methodology / template / skill 對應的原始專案位置（公司機器）：`~/Desktop/project_claude/`。
本 repo 已刪去所有具體 schema／門市名／真實數字／內部連結（例外：`skills/store-handover-impact/`，使用者授權保留真實名稱）。

## Playbooks

| 本 repo 檔案 | 來源專案 |
|-------------|---------|
| playbooks/hypothesis-falsification.md | traffic_ham / traffic_attribution / tainan_ms%_yongkang_change |
| playbooks/multi-track-analysis-management.md | 26H1_ob_rs_bonus_review |
| playbooks/government-api-integration.md | motc_vehicle_survey_handoff |
| playbooks/db-to-sheet-audit-automation.md | govern_routine_work |
| playbooks/incident-log-management.md | bi-security-scan（CVE 事件處理 14 條原則，抽象為跨事件 incident log pattern） |
| playbooks/report-maintenance-sop-skeleton.md | key_report_sop（報表維修 SOP 固定章節 + 症狀跳點 + 可 copy 指令） |
| playbooks/share-change-attribution.md | 2026_reg_forecast / playbook_brand_share_mom_analysis（share Δpp 拆到車款、洞 vs 補血、五類型判可持續） |
| playbooks/funnel-failure-fingerprint-clustering.md | rs_sales_track/門市分群與輔導方案（最上游失守點指派主群 + 併發症指紋 + 可回收總表） |

## Frameworks

| 本 repo 檔案 | 來源專案 |
|-------------|---------|
| frameworks/funnel-ranking-diagnosis.md | rs_sales_intelligence_center + rs_sales_track + 26H1_ob_rs_bonus_review |
| frameworks/three-layer-management-loop.md | rs_mgmt_loop (04/05/06) |
| frameworks/product-diagnostic-nine-step-and-eol-gates.md | market_info / vehicle_diagnostic playbook |
| frameworks/incentive-system-diagnosis.md | 26H1_ob_rs_bonus_review |
| frameworks/traffic-light-design-pattern.md | traffic_light / 26H1_ob_rs_bonus_review |
| frameworks/ai-advisory-system-design.md | store_manager_action PRD |
| frameworks/multi-timepoint-forecast.md | mvo_forecast（機車領牌預測三時點 × 多情境） |

## Methodologies

| 本 repo 檔案 | 來源專案 |
|-------------|---------|
| methodologies/verifiable-judgment-framework-writing.md | store-handover-impact / judgment-framework.md meta 抽象 |
| methodologies/exogenous-attribution-restoration.md | traffic_attribution（雨對 traffic 影響案） |
| methodologies/population-penetration-decomposition.md | impact_of_declining_birth_rates_on_the_moto_market |
| methodologies/ai-parallel-first-architecture.md | richard_handover（ICC 重構 framework-learning-guide 的 meta 心法） |
| methodologies/weak-model-deterministic-validation.md | sales_pulse_training/chatbot plan（弱模型 + 程式驗證 + 四階段管線） |
| methodologies/purposive-sampling-for-system-validation.md | cctv 門市計數驗證（目的性抽樣四條件 + 誠實邊界） |
| methodologies/judgment-framework-evolution-tracking.md | tainan_ms%_yongkang_change NOTE-報告版本與判準演化（判準從紙面到執行的漏東西 pattern） |
| methodologies/redteam-self-challenge.md | market_info/strategy/redteam_findings（兩 subagent 挑戰自己論點、四級分類、收回/改口表） |
| methodologies/code-sanitization-for-handover.md | gsh_data_playbook/07_sanitization_process（原檔不碰 + regex 替換 + audit report + 業務邏輯保留） |

## Templates

| 本 repo 檔案 | 來源專案 |
|-------------|---------|
| templates/forecast-three-propositions.md | 2026_reg_forecast |
| templates/data-flow-playbook-skeleton.md | gsh_data_playbook |
| templates/bi-knowledge-base-structure.md | bi-knowledge-base |
| templates/business-diagnosis-narrative-skeleton.md | rs_sales_track 2026 業績診斷 v2 |
| templates/handover-doc-skeleton.md | sales_review extender HANDOVER（低頻任務交接入口骨架） |
| templates/lightweight-team-tracker.md | bi_team_tracker（3-5 人團隊 Sheets + Apps Script + AI 取代 JIRA） |
| templates/ai-human-collaborative-prd-skeleton.md | app_video/app_update_sales_pulse PRD（6-phase AI × 人協作 PRD 骨架） |
| templates/hypothesis-check-meeting-note.md | rs_sales_track/會議紀錄/老闆業績檢討會（會議假說→資料檢驗→回會骨架） |
| templates/ai-session-handoff-doc.md | bi-knowledge-base/_working/playbook-plan（11 節 context pack 給下 session） |

## References / Architecture

| 本 repo 檔案 | 來源專案 |
|-------------|---------|
| references/architecture/offline-build-static-json-pattern.md | incentive_control_center / rs_sales_intelligence_center |
| references/architecture/activity-folder-self-contained-pattern.md | incentive_control_center |
| references/architecture/nl-to-sql-agent-layering.md | sales-pulse-agent |
| references/architecture/claude-md-navigation-pattern.md | bi-pipelines（monorepo CLAUDE.md 導航 + ADR + cross-repo artifact） |
| references/architecture/internal-ai-tool-framework-pattern.md | bi-ai-framework（6 層分工 + MR 序列 + 公開契約凍結時機） |
| references/architecture/scheduled-task-unification-pattern.md | GSH_Automation（core 共用 + tasks 一檔一任務 + 三層執行堆疊 + Mac dev / VM prod 分離） |

## Skills

| 本 repo 檔案 | 來源專案 |
|-------------|---------|
| skills/store-handover-impact/ | tainan_ms%_yongkang_change |
| skills/validating-replacement-data-sources/ | registration_data_check |
| skills/decomposing-market-decline/ | impact_of_declining_birth_rates_on_the_moto_market |

---

**總計：42 件抽自約 34 個原始專案（五輪 35 件 + Pass 1 兩批 5 件 + Pass 2 兩件，2026-11-19）。**
