---
title: 每場活動自成一個資料夾 pattern — 多活動 BI app 的組織方式
version: v1
last-updated: 2026-11-04
source: incentive_control_center（去識別化）
---

# 每場活動自成一個資料夾 pattern

> 做促案控制台、競賽排行、A/B 測試…這類「多活動並行、每場規則不同」的 BI app 時，最糟的做法是做一個「可配置的 engine」。這份文件說明為什麼每場活動應該**自成一個資料夾**，不共用 engine，以及怎麼組織。

## 情境（什麼時候拿出來用）

- BI app 要承接「不斷有新場活動要上」
- 每場活動規則不同、算法不同、追蹤指標不同
- 想避免「engine 越改越複雜、每改一次都怕壞舊活動」
- 想讓每場活動的 spec、算法、資料、產出**在一個資料夾內看完**

## 核心主張

**反直覺**：不要做 engine。

**為什麼**：
- Engine 的參數會隨新活動一直加，變成「有 50 個參數的 config」
- 改 engine 的 bug 會影響歷史活動
- 讀一個活動要跨 engine + config 兩處
- 誰都不敢改 engine，最後所有邏輯都 fork 到 config

**改成**：每場活動 = 一個資料夾，**自成一體**（算法、資料、產出全在裡面），不共用 engine，新活動 = **複製範本改 CONFIG**。

---

## 骨架：activity/ 資料夾結構

```
activity/<activity-id>/
├── spec/
│   ├── README.md                   ★ SSOT（算法規格 + 計分範例 ≥ 3 筆）
│   └── <活動規則>.pdf              BP 規則文件（前端提供下載）
├── app/
│   ├── read_13m.py                 該活動的 IO 層（COLMAP、日期 parse、過濾）
│   └── compute.py                  算分 + 組 JSON shape
│                                   頭段是 §1 CONFIG BLOCK（META / TRACKS / TARGET_MODEL）
├── data/
│   ├── sample-13m.csv              committed schema 參考檔（pipeline 不消費）
│   ├── 13m.csv                     gitignored，Tableau Prep 產出
│   ├── targets.csv                 活動目標設定
│   ├── <name>.tfl                  committed Tableau Prep flow
│   └── manual/                     人工維護的補充檔（groups.csv…）
└── tracks.json                     tab 定義（前端用）

tests/baselines/<activity-id>.json  snapshot test baseline（放外面，便於跑 pytest）
tests/test_compute_<aid>.py         snapshot test
```

**鐵則**：
- **每個活動資料夾自洽**：算法、資料、產出全在裡面
- 活動之間**不共用 engine**（可以共用 `src/pipeline/` 編排、但不共用算法）
- 新活動 = **複製舊活動資料夾**、改名、改 CONFIG、改 spec

---

## compute.py 的 CONFIG block

每個 `compute.py` 的頭段是結構化 CONFIG：

```python
# §1 CONFIG BLOCK
# 所有「這個活動特有」的變數都在這，動其他段要先問

META = {
    "activity_id": "<activity-slug>-<year>",
    "activity_name": "<活動名>",
    "period_start": "2026-06-01",
    "period_end": "2026-08-31",
    ...
}

TRACKS = {
    "track_id_A": {
        "display_name": "...",
        ...
    },
    ...
}

TARGET_MODEL = {
    "method": "...",
    "coefficients": {...},
    ...
}

# §2 以下算法不要動（除非有結構性變動）
def compute(root):
    cfg = dict(META=META, TRACKS=TRACKS, ...)
    ...
```

**原則**：
- 新活動**只動 CONFIG block**，其他段不動
- CONFIG 之外的算法段應該「活動類型通用」
- 若新活動要改算法段 → 該算法已不通用 → 這個活動要**分支一個新 base 範本**

---

## 複製新活動的流程

```
1. 複製 activity/<最近一檔>/ → 改名 activity/<new-id>/
2. 改 spec/README.md（SSOT）：
   - 活動概要 + 計算規格 + 計分範例 ≥ 3 筆
3. 改 app/compute.py 的 §1 CONFIG BLOCK：
   - META / TRACKS / TARGET_MODEL
   - 其他段不動
4. 換 data/sample-13m.csv 成該活動週期的 schema snapshot
5. 寫 snapshot test tests/test_compute_<aid>.py
   - baseline 放 tests/baselines/<aid>.json
6. 跑 pytest 守綠
```

**鐵則**：
- Spec 先寫、再改 code
- Spec 裡的「計分範例」是 code 的驗收測試
- Snapshot test baseline 每次跑完確認（改 CONFIG 時要 regenerate）

---

## 共用什麼、不共用什麼

| 項目 | 共用？ |
|------|------|
| Pipeline 編排（build / push） | ✅ 共用（`src/pipeline/`） |
| 資料契約（JSON shape） | ✅ 共用 |
| 前端渲染 lib | ✅ 共用 |
| 權限／部署架構 | ✅ 共用 |
| **算法（compute.py）** | ❌ **不共用** |
| **CONFIG** | ❌ **不共用** |
| **IO 層（read_13m.py）** | ❌ **不共用**（容許活動間 schema 差異） |

**為什麼算法不共用**：
- 加碼活動的規則常常「差一個細節」就違反共用性
- 通用化會把一堆 edge case 塞進 engine
- **寧可複製貼上**，也不要早期通用化

---

## 落地準則 6 條（MUST/SHOULD/MUST NOT）

每場活動必須：

1. **MUST** 有 `spec/README.md` 含計分範例 ≥ 3 筆（當測試驗收）
2. **MUST** 有 `app/compute.py` 頭段 §1 CONFIG BLOCK
3. **MUST** 有 snapshot test baseline
4. **MUST NOT** 動 `src/pipeline/*`（共用的）
5. **SHOULD** 複製最近一檔活動當範本（不要從零寫）
6. **SHOULD** 一週內無需上 production 就跑 preview 給 BP 看

**違反任何一條就是 bug**。

---

## snapshot test 的角色

```python
# tests/test_compute_<aid>.py
def test_compute_matches_baseline():
    result = compute(ACTIVITY_ROOT)
    assert result == json.load(BASELINE_PATH)
```

**作用**：
- 改算法前先跑 → baseline 綠
- 改算法後跑 → 預期變紅（看差異）
- 故意改 baseline → 承認「是我改的」
- 不小心改 pipeline 動到別活動 → 紅

**原則**：
- Baseline 當資料存，不當 code 讀
- Baseline 更新要跟 PR 的 code 改動同一 commit
- 新活動上線時 baseline 要 freeze 一份

---

## 常見陷阱

| 陷阱 | 症狀 | 校正 |
|------|------|------|
| 做 engine | 改一次怕壞舊活動 | 每活動自成一夾 |
| 共用 config | 50 個參數擠一處 | CONFIG 在 compute 頭段 |
| 新活動從零寫 | 犯過的坑再犯一次 | 複製最近一檔 |
| 無 spec | 算法不可驗收 | spec 計分範例 ≥ 3 筆 |
| 無 snapshot test | 改一次怕回歸 | baseline + snapshot |
| 動 pipeline 偷塞邏輯 | 影響其他活動 | pipeline 不改、邏輯進 compute |
| 共用算法段 | 一個 bug 全部活動 | 不早期通用化 |
| 跳過 spec 直接改 code | 規格飄移 | spec 先寫 |

---

## 檢核清單（新活動上線前對一次）

- [ ] 複製最近一檔活動當範本？
- [ ] 改 `spec/README.md` 含計分範例 ≥ 3 筆？
- [ ] 改 `app/compute.py` §1 CONFIG block？
- [ ] 其他段**沒動**？
- [ ] 換 `data/sample-13m.csv` 當 schema reference？
- [ ] 寫 snapshot test + baseline？
- [ ] pytest 綠？
- [ ] preview 跑過給 BP 看？

---

## 相關

- [[offline-build-static-json-pattern]] — 這份的 pipeline 跑在那個架構上
- [[multi-track-analysis-management]] — 若活動多到要四線並行，配那份

## 真實案例骨架（去識別化）

### 案例 1：engine 走向絕路
原本做了一個 unified engine 處理「所有加碼活動」。做到第 4 場活動時，CONFIG 已有 47 個參數，改任何一個都要跑全部活動的 snapshot test。新活動上線前要花半天 review 不小心改到的地方。
**改成每活動一夾**後：每活動 compute.py 150-200 行、CONFIG block 20-30 參數、新活動複製改 CONFIG 2-3 小時上線。

### 案例 2：第 3 場活動需要不同 TARGET_MODEL
Engine 時：要加一個 `target_method` 參數，engine 內 if/else。
每活動一夾時：第 3 場的 `compute.py` 直接改 `TARGET_MODEL` 段，別人無感。

### 案例 3：snapshot test 救命
某次改共用 pipeline，不小心動到了 JSON 寫檔順序。snapshot test 整排紅，10 分鐘發現，不用等 BP 檢查。

### 案例 4：複製範本降低新人上手
新人上線新活動前，只需讀一場過往活動的資料夾，看懂 spec + compute + sample 三件事。約 1 天上手，不用先讀 engine 規格書。
