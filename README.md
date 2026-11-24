# Alston Playbook

個人方法論、框架、分析套路的沉澱。從過往工作中萃取，去識別化，可攜式。

## 原則

- **只放可攜內容**：方法論、框架、判準、模板、playbook。raw data／內部 schema／客戶名單一律不入 repo。
- **去識別化**：公司名、品牌、產品、人名、數字一律 placeholder 或區間化。
- **可驗證**：每個框架附使用情境、步驟、判準、常見陷阱、相關框架。
- **連結式知識**：框架間用 `[[框架名]]` 相互引用。

## 目錄結構

```
alston-playbook/
├── README.md
├── CONTRIBUTING.md          # 去識別化規則、撰寫規範
├── INDEX.md                 # 全框架索引（主題分類）
├── frameworks/              # 可複用決策框架、判準、拆解邏輯
├── methodologies/           # 分析方法論（通用做法，比 framework 更底層）
├── playbooks/               # 面對特定問題類型的執行手冊
├── skills/                  # Claude Code / Agent skill（可直接 drop-in）
├── templates/               # 報告、PRD、SOP 範本
├── glossary/                # 術語表（我自己的 vocab）
└── references/              # 外部參考資料、書單、思考法
```

## 使用方式

**三種查法**：
1. **按情境查**（新公司會遇到的事）→ [SCENARIOS.md](SCENARIOS.md)
2. **按產物類型查** → [INDEX.md](INDEX.md)
3. **按來源專案查** → [references/source-projects-map.md](references/source-projects-map.md)

產物類型速查：

| 情境 | 去哪裡 |
|------|-------|
| 遇到新案子，想找類似的分析套路 | `INDEX.md` → `frameworks/` |
| 要寫報告、PRD、SOP | `templates/` |
| 要給 Claude 一個 skill 用 | `skills/` |
| 要重讀某個方法本身的來龍去脈 | `methodologies/` |
| 遇到具體問題類型（例：業績衰退） | `playbooks/` |

## 現況（2026-11-19）

- `frameworks/`：7 件 ✅（排序診斷 / 三層迴路 / 單產品 9 步 + EOL / 獎金制度 / 紅綠燈 / AI 行動建議 / 多時點預測）
- `methodologies/`：9 件 ✅（判準撰寫 meta / 外生變數歸因 / 人口 × 滲透率拆解 / AI-first 平行開發 / 弱模型確定性驗證 / 目的性抽樣驗證 / 判準演化追蹤 / 紅隊自我挑戰 / **原始碼脫敏**）
- `playbooks/`：8 件 ✅（假設反證 / 多線並行管理 / 政府 API / DB → Sheet 稽查 / 事件簿管理 / 報表維運 SOP / 份額變化歸因 / **漏斗失守指紋分群**）
- `templates/`：9 件 ✅（預測三命題 / 資料流 F1-F4 / BI 知識庫 / 業績診斷敘事 / HANDOVER 骨架 / 輕量團隊 tracker / AI × 人協作 PRD / 假說檢驗會議紀錄 / **AI session 交接**）
- `references/architecture/`：6 件 ✅（離線 build → JSON / 活動自成一夾 / NL → SQL agent / CLAUDE.md 導航 / 內部 AI 工具框架化 / **排程任務統一框架**）
- `skills/`：3 件 ✅（store-handover-impact / validating-replacement-data-sources / decomposing-market-decline）

**總計：42 件（五輪 35 件 + Pass 1 兩批 5 件 + Pass 2 近週新增 2 件）。**

## 來源

本 repo 從 Gogoro BI 任期（2024–2026）33+ 專案中萃取。原始專案（含公司資料）保留在工作電腦，不會進入本 repo。對應關係見 `references/source-projects-map.md`。
