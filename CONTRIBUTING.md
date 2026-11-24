# CONTRIBUTING — 撰寫規範與去識別化規則

## 去識別化規則（鐵則）

寫入前把下列全部替換掉：

| 原始類型 | 替換 |
|---------|------|
| 前東家名（Gogoro / GoShare） | `<Company>` 或產業泛稱 `<EV-brand>` |
| 競品品牌（SYM / KYMCO / YAMAHA） | `<Brand A>` / `<Brand B>` / `<Brand C>` |
| 真實門市名（永康、海佃…） | `<Store #1>` |
| 真實縣市（若數字一起出現） | `<City North>` / `<City South>` 或刪 |
| 業務 / 加盟主姓名 | `<Rep A>` / `<Franchisee B>` |
| 同事姓名 | `<Lead>` / `<Analyst>` |
| BQ schema（`gogoro-twbi-dw.GGR_AI.Store`） | `<project>.<dataset>.<table>` |
| 內部欄位名（`bo_calendar_week` 等） | 若是通用概念保留，若是內部命名改通用（`fiscal_week`） |
| 實際數字（領牌量、達成率、獎金） | 區間（`~70-80%`）或拿掉數字只留趨勢 |
| 內部連結（Google Drive / Slack） | 刪 |
| 日期（含敏感時點） | 相對時間（T0 / T0+3M）或模糊化 |

## 檔案撰寫模板

### Framework 卡

```markdown
# [框架名]

> 一句話定位

## 情境（什麼時候拿出來用）
什麼問題、什麼徵兆

## 核心框架
決策樹／拆解邏輯／層次

## 步驟
1. ...
2. ...

## 判準／門檻
- 什麼情況算 ok／warning／red

## 常見陷阱
- 陷阱 ← 校正方式

## 真實失敗案例（去識別化）
短段落敘述

## 可複用模板
路徑連結

## 相關
[[其他框架]]
```

### Methodology 文件

比 framework 更底層。寫「為什麼這套方法成立」「適用邊界」「與其他方法對比」。

### Playbook

針對特定問題類型，寫執行手冊。有具體的「拿到問題後，先做 A，再做 B」順序。

### Skill

照 Claude Code skill 規範寫（SKILL.md + references/ + scripts/）。

## 連結規範

- 相互引用用 `[[name]]`，`name` 是另一份檔案的檔名（不含 `.md`）
- 不存在的 `[[name]]` ok，當 todo

## 版本

- 用 git 管版本
- 大改動在檔頭加 `last-updated: YYYY-MM-DD`
- 推翻舊結論的 commit message 寫 `revise:` prefix

## 不要做

- 不要把這個 repo push 到公司 GitLab／任何公司管控的雲端
- 不要在公司機器上 git clone 工作 raw data 進來
- 不要寫「某年某月某客戶怎麼了」——寫「這類情境下」
