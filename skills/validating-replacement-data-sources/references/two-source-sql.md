# 兩個資料源怎麼接起來查

`data-source-migration-check` 的參考檔。實際動手時讀這一份。

## Tableau `.tdsx` / `.hyper`

`.tdsx` 是 zip，extract 放在 `Data/Extracts/`：

```bash
python3 -m venv .venv && .venv/bin/pip install tableauhyperapi openpyxl

mkdir -p tmp/hyper
unzip -o -j input/new_source.tdsx "Data/Extracts/*" -d tmp/hyper
unzip -o -j input/old_source.tdsx "Data/Extracts/*" -d tmp/hyper
```

資料表固定叫 `"Extract"."Extract"`。取 schema：

```python
from tableauhyperapi import Connection, HyperProcess, TableName, Telemetry

with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
    with Connection(hyper.endpoint, "tmp/hyper/new_source.hyper") as conn:
        td = conn.catalog.get_table_definition(TableName("Extract", "Extract"))
        for c in td.columns:
            print(c.name.unescaped, c.type)
```

**注意**：`get_table_definition` 只吃 `TableName` 物件，餵 tuple 會噴
`Specified table does not exist`。

## 把兩份 `.hyper` 掛在同一個連線

這是整套做法的關鍵 —— 掛上去之後就能用一句 SQL 做逐列比對，不用把資料拉進 Python：

```python
from pathlib import Path
from tableauhyperapi import Connection, HyperProcess, Telemetry

with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
    with Connection(hyper.endpoint) as conn:          # 注意：不帶 database 參數
        conn.catalog.attach_database(Path("tmp/hyper/old_source.hyper"), "old")
        conn.catalog.attach_database(Path("tmp/hyper/new_source.hyper"), "new")
        conn.execute_list_query('SELECT COUNT(*) FROM new."Extract"."Extract"')
```

**join 一定要加 `COLLATE "root"`**，兩份 extract 的 collation 常常不一致：

```sql
FROM new."Extract"."Extract" n
JOIN old."Extract"."Extract" o
  ON n.vin = o."VIN車身代碼" COLLATE "root"
```

字串比較也要加：`CAST(o.a AS TEXT) = CAST(n.b AS TEXT) COLLATE "root"`。
中文欄名要用雙引號包起來。

**一個查詢炸掉會讓整個 transaction 進入 aborted 狀態**，後續查詢全部失敗並回
`current transaction is aborted`。把每個區段包成獨立函式、各自 try，或分次跑。

**Hyper 沒有 `Date.now()` 之類的東西，但有標準 SQL 的 `FILTER (WHERE ...)`** ——
一次查詢算多個條件的計數就靠它，比跑十次查詢快得多。

## 腳本骨架

一支腳本產出全部數字，輸出 TSV，區段用 `### 標題` 分隔。
文件與 xlsx 都從這份 TSV 讀，**任何數字都不在別的地方重打一次**。

```python
def emit(conn, title, sql, header):
    print(f"\n### {title}")
    print("\t".join(header))
    for row in conn.execute_list_query(sql):
        print("\t".join("" if v is None else str(v) for v in row))
```

下游解析：

```python
def load_sections(path):
    sections, cur = {}, None
    for line in Path(path).read_text().splitlines():
        if line.startswith("### "):
            cur = line[4:].strip(); sections[cur] = []
        elif line.strip() and cur:
            sections[cur].append(line.split("\t"))
    return sections
```

## 查詢模板

以下 `{N}` = 新源資料表、`{O}` = 舊源、`{J}` = join 後、`{Y}` = 期間條件。

### A 類：逐日缺漏

```sql
SELECT o.date_col, COUNT(*) FROM {O} o
WHERE {Y}
  AND NOT EXISTS (SELECT 1 FROM {N} n WHERE n.date_col = o.date_col)
GROUP BY 1 ORDER BY 1
```

### A 類：批次欄位追檔

```sql
SELECT n.source_file, MIN(n.date_col), MAX(n.date_col), COUNT(*)
FROM {N} n WHERE n.date_col BETWEEN <缺漏前一週> AND <缺漏後一週>
GROUP BY 1 ORDER BY 2
```

看相鄰批次：檔名跳號 = 整檔沒載；檔名在但 `MAX(date)` 提早結束 = 只載一半。

### B 類：逐欄有值率（掃全部欄位）

```python
total = q(f"SELECT COUNT(*) FROM {N} n WHERE {Y}")[0][0]
for c in cols:
    nn, dv = q(f'SELECT COUNT("{c}"), COUNT(DISTINCT "{c}") FROM {N} n WHERE {Y}')[0]
    print(c, nn, f"{100.0*nn/total:.3f}%", dv)
```

`COUNT(col)` 不計 NULL，所以它就是「有值筆數」。

### D 類：逐欄相符率

```sql
SELECT
  COUNT(*) FILTER (WHERE o."{oc}" IS NOT NULL AND n."{nc}" IS NOT NULL),
  COUNT(*) FILTER (WHERE o."{oc}" IS NOT NULL AND n."{nc}" IS NOT NULL
                     AND CAST(o."{oc}" AS TEXT) = CAST(n."{nc}" AS TEXT) COLLATE "root"),
  COUNT(*) FILTER (WHERE o."{oc}" IS NULL AND n."{nc}" IS NOT NULL),
  COUNT(*) FILTER (WHERE o."{oc}" IS NOT NULL AND n."{nc}" IS NULL)
FROM {J} WHERE {Y}
```

四個數字缺一不可：可比列數、相符列數、舊空新有、舊有新空。
只報相符率會把「新源補了值」跟「新源掉了值」混在一起。

### D 類：差值分布（找時間函數）

```sql
SELECT n.num_col - o.num_col AS diff, COUNT(*)
FROM {J} WHERE {Y} AND n.num_col IS NOT NULL AND o.num_col IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

差值集中在單一非零值 = 系統性偏移，不是隨機錯誤。再依年度切開確認是不是時間函數。

### D 類：分類欄交叉表

```sql
SELECT o.cat_col, n.cat_col, COUNT(*) FROM {J} WHERE {Y}
GROUP BY 1,2 ORDER BY 3 DESC LIMIT 20
```

再各自與底層欄位交叉，新規則就會浮出來：

```sql
SELECT n.cat_col, n.underlying_col, COUNT(*) FROM {N} n WHERE {Y} GROUP BY 1,2
```

### D 類：內部等式檢驗

```sql
SELECT COUNT(*) AS n,
  COUNT(*) FILTER (WHERE c = a - b),
  COUNT(*) FILTER (WHERE c = a + b),
  COUNT(*) FILTER (WHERE a = c - b),
  COUNT(*) FILTER (WHERE a = c + b),
  COUNT(*) FILTER (WHERE c - a = b),
  COUNT(*) FILTER (WHERE c - a = -b)
FROM {N} n WHERE {Y}
  AND a IS NOT NULL AND b IS NOT NULL AND c IS NOT NULL
  AND b <> 0            -- 排除退化列，否則命中率虛高
```

等式都是 0 的時候，再看差額的形狀：

```sql
SELECT CASE WHEN c = 0 THEN 'c=0'
            WHEN c - a BETWEEN 1 AND 9999 THEN '小額正值'
            WHEN c - a >= 10000 THEN '大額正值'
            WHEN c - a = 0 THEN '相等'
            ELSE '負值' END AS bucket,
       COUNT(*), COUNT(DISTINCT c - a), MIN(c - a), MAX(c - a)
FROM ... GROUP BY 1
```

`COUNT(DISTINCT 差額)` 是關鍵：**相異值只有幾個 = 固定費率；上百個 = 另一個口徑**。
再確認同樣的差額值在 `b = 0` 與 `b <> 0` 的列上都出現 —— 都出現就代表差額與 `b` 無關。

### E 類：前後空白與大小寫

```sql
SELECT COUNT(*) FILTER (WHERE n.txt <> TRIM(n.txt)) FROM {N} n WHERE {Y}
```

差異中有多少是純空白：

```sql
SELECT COUNT(*) FILTER (WHERE TRIM(CAST(o.a AS TEXT)) = TRIM(CAST(n.b AS TEXT)) COLLATE "root")
         AS whitespace_only,
       COUNT(*) AS all_diff
FROM {J} WHERE {Y} AND CAST(o.a AS TEXT) <> CAST(n.b AS TEXT) COLLATE "root"
```

### E 類：業務鍵重複、未配對列

```sql
SELECT COUNT(*) FROM (SELECT key FROM {N} n WHERE {Y} GROUP BY 1 HAVING COUNT(*) > 1) t;

SELECT COUNT(*) FROM {N} n WHERE {Y}
  AND NOT EXISTS (SELECT 1 FROM {O} o WHERE o.key = n.key COLLATE "root");
```

未配對的那批要往下看它們的共同特徵（同一個代碼、同一個批次），
通常會直接指出一個 E 類問題。

### 補值可行性：對照是不是 1 對 1

要用 A 欄補 B 欄之前，先驗證對照關係：

```sql
WITH m AS (SELECT n.zip AS z, o.city AS city, COUNT(*) AS c FROM {J} WHERE {Y} GROUP BY 1,2)
SELECT z, city, c FROM m WHERE z IN (SELECT z FROM m GROUP BY z HAVING COUNT(*) > 1)
ORDER BY z, c DESC
```

多對一的那幾組，看每組的次要值有幾列 —— 只有一兩列通常是舊源的個案錯誤，
補值仍然安全；成千上百列就是真的多對一，不能補。

**CTE 比子查詢重複寫兩次可靠** —— 在 Hyper 裡把同一段 join 子查詢貼兩次
容易踩到 alias 衝突。

## 產 xlsx

用 `openpyxl`，排版規則見 `analysis-xlsx-output-skill` 的
`references/excel-report-layout.md`。這個場景特有的幾點：

- 佐證分頁直接讀檢核腳本的 TSV，**不要在 xlsx 產生器裡重打數字**
- 問題清單的「處理狀態」用 `DataValidation` 做下拉：

  ```python
  from openpyxl.worksheet.datavalidation import DataValidation
  dv = DataValidation(type="list",
                      formula1='"未開始,查證中,已修,不修（附理由）,不是問題"',
                      allow_blank=True)
  ws.add_data_validation(dv); dv.add("I4:I26")
  ```

- 嚴重度欄依值上底色（紅／橘／黃），不要用圖示集（轉進 Google Sheet 會掉）
- 差異率 0 不要寫成 `+0.0%`；會四捨五入成 0.0% 的非零值寫 `≈0%`
