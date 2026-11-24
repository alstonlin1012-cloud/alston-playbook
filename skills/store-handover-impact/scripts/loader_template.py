"""據點易主影響分析 — 參數化 loader 骨架。

用法：複製這個檔到專案的 scripts/ 底下，只改最上面的 CONFIG，其餘不動。
本檔**不含任何特定案件的常數**（公司名、門市名、交接日）——那些是分析腳本的事。

內建的自檢會在 load() 時自動跑，每一項都對應一個實測踩過的坑：
  1. 編碼／分隔符          → 讀不進來會直接炸，不會靜默
  2. 無欄名的數量欄        → 用位置取，不靠欄名
  3. 千分位逗號            → 先去逗號再轉數值，轉完驗 NaN 必須為 0
  4. 剔除規則              → 印出剔了幾列**與幾台**（列數少不代表量體小）
  5. 未結束的當期          → 印出最後一期的量體，要你自己確認完不完整
  6. 未歸屬據點            → **分期**算比例（全期會稀釋掉窗口內的真實缺口）
  7. 經營者欄是否帶歷史    → 這條錯了不會報錯，只會讓你把前任的業績算進接手方
  8. 期間內開／關的據點    → 基期干擾，會讓群組成長率失真
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict

# ─────────────────────────────────────────────────────────────
# CONFIG — 只改這裡
# ─────────────────────────────────────────────────────────────

CONFIG = {
    "path": "data/reg_data.csv",

    # 檔案格式。Tableau 匯出常見 utf-16 + tab；一般 CSV 用 utf-8-sig + ","
    "encoding": "utf-16",
    "delimiter": "\t",

    # 欄位映射：語意名 → **欄名（str，優先）** 或位置（int）。
    #
    # ★ 一律優先用欄名。實測踩過的坑：同一個 worksheet 重新匯出後，
    #   欄序會變、欄位會整個消失（本專案的 tainan_reg_data 就從 9 欄
    #   變 8 欄、門市欄消失、期別欄從 [3] 移到 [2]）。寫死位置＝下次
    #   匯出就 IndexError，或更糟：讀到別的欄而不報錯。
    #
    # 特殊值：
    #   "__LAST__"  → 最後一欄（Tableau 的度量欄常常沒有欄名）
    #   None        → 這份資料沒有這個欄位，相關模組自動跳過
    "columns": {
        "region":   "MVO_City",         # 縣市／大區
        "period":   "MVO_Year month",   # 期別，如 YYYYMM
        "subarea":  None,               # 行政區（沒有就 None，模組 E 跳過）
        "brand":    "GTM_KeyBrand",     # 品牌欄（自家 vs 競品）
        "tag":      "tag_wemo",         # 輔助標籤欄——剔除規則要用到就得映射
        "store":    None,               # 「公司-據點」；這份匯出沒有 → None
        "qty":      "__LAST__",         # 數量（無欄名，取最後一欄）
    },

    # 「公司-據點」的分隔符。設 None 表示該欄只有據點名、沒有公司。
    "store_company_sep": "-",

    # 自家品牌在 brand 欄的值。市占率分子用它，分母用全部。
    "own_brand": "GOGORO",

    # 剔除規則：list of (columns 裡的**語意 key**, 要剔除的值集合, 說明)
    # 用語意 key（不是位置、不是欄名），欄序變動時自動跟著走。
    "exclusions": [
        ("tag",   {"WEMO"},     "共享車隊（非零售通路）"),
        ("brand", {"", "TBD"},  "品牌未定"),
    ],

    # 未結束／不完整的期別，一律排除。**每次重跑都要重新確認。**
    "exclude_periods": ["202607"],

    # 非據點的佔位字串（例：目標縣市以外的列，門市欄填「非台南市」）。
    # 這些不是「未歸屬」，是「本來就不提供」，計算未歸屬比例時要排除。
    "store_placeholders": {"非台南市"},
}


# ─────────────────────────────────────────────────────────────
# 通用工具
# ─────────────────────────────────────────────────────────────

def _to_int(v):
    """數量轉整數。處理千分位逗號、空字串、全形空白。

    注意：不要用 pd.to_numeric(errors='coerce')——它會把 '1,021' 靜默轉成
    NaN，而帶逗號的通常正好是量體最大的那些列。
    """
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace("　", "")
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def resolve_columns(cfg, header):
    """把 CONFIG 的欄位映射解析成「語意名 → 位置」，並在對不上時大聲報錯。

    支援：欄名（str）、位置（int）、"__LAST__"（最後一欄）、None（無此欄）。

    ★ 為什麼要這個函式：實測中資料檔重新匯出後欄序變了、欄位消失了，
      寫死位置會 IndexError（好的情況）或**靜默讀到別的欄**（壞的情況）。
      這裡一次解析完並驗證，讓問題在讀檔當下就浮現。
    """
    resolved, missing = {}, []
    for key, spec in cfg["columns"].items():
        if spec is None:
            resolved[key] = None
        elif spec == "__LAST__":
            resolved[key] = len(header) - 1
        elif isinstance(spec, int):
            resolved[key] = spec if spec < len(header) else None
            if resolved[key] is None:
                missing.append(f"{key}=位置{spec}（檔案只有 {len(header)} 欄）")
        elif spec in header:
            resolved[key] = header.index(spec)
        else:
            resolved[key] = None
            missing.append(f"{key}={spec!r}")

    if missing:
        raise KeyError(
            "CONFIG['columns'] 有欄位在檔案裡找不到：\n  "
            + "\n  ".join(missing)
            + f"\n\n檔案實際的欄位是：\n  {header}\n\n"
            "這通常代表資料被重新匯出、欄序或欄位變了。"
            "請對照實際欄位更新 CONFIG——不要猜位置。"
        )
    return resolved


def _col(row, key, cfg, header, resolved=None):
    """依解析後的欄位映射取值。"""
    idx = (resolved or resolve_columns(cfg, header)).get(key)
    if idx is None:
        return ""
    return row[idx].strip() if idx < len(row) else ""


def load(cfg=CONFIG, verbose=True):
    """讀檔 → 清洗 → 自檢。回傳 list[dict]。

    每筆包含：region / period / subarea / brand / store_raw / company /
             store_name / qty
    """
    with open(cfg["path"], encoding=cfg["encoding"], newline="") as f:
        reader = csv.reader(f, delimiter=cfg["delimiter"])
        header = next(reader)
        raw = [r for r in reader if r]

    ncols = len(header)
    resolved = resolve_columns(cfg, header)   # ← 對不上就在這裡炸，不會靜默讀錯欄
    rows, bad_qty = [], 0

    if verbose:
        print(f"欄位對應（共 {ncols} 欄）：")
        for k, i in resolved.items():
            print(f"  {k:8s} → {'（無此欄）' if i is None else f'[{i}] {header[i]!r}'}")

    for r in raw:
        if len(r) < ncols:
            continue
        qty = _to_int(_col(r, "qty", cfg, header, resolved))
        if qty is None:
            bad_qty += 1
            continue

        store_raw = _col(r, "store", cfg, header, resolved)
        sep = cfg["store_company_sep"]
        if sep and sep in store_raw:
            company, store_name = store_raw.split(sep, 1)
        else:
            company, store_name = "", store_raw

        # 動態存入 CONFIG 映射的每個欄位（tag 之類的輔助欄也在內），
        # 剔除規則才取得到值。qty 已另外解析為 int。
        rec = {key: _col(r, key, cfg, header, resolved)
               for key in cfg["columns"] if key not in ("qty", "store")}
        rec.update(store_raw=store_raw, company=company,
                   store_name=store_name, qty=qty)
        rows.append(rec)

    if verbose:
        print(f"讀入 {len(rows)} 列（原始 {len(raw)}）")
        if bad_qty:
            print(f"  ⚠ {bad_qty} 列數量無法解析，已跳過——確認不是千分位逗號沒處理")
        if resolved.get("store") is None:
            print("  ⚠ 這份資料**沒有據點欄** → 模組 D/E/F 的門市層分析做不了，")
            print("    check_operator_history() 與 check_store_churn() 會跳過。")

    rows = _apply_exclusions(rows, header, cfg, verbose)
    if verbose:
        _report_last_period(rows, cfg)
    return rows


def _apply_exclusions(rows, header, cfg, verbose):
    """套用剔除規則與期別排除，並印出**列數與量體**。

    剔除規則用 columns 裡的語意 key 指定欄位，所以欄序變動時自動跟著走。
    """
    for key, values, note in cfg["exclusions"]:
        if not rows:
            break
        if key not in rows[0]:
            raise KeyError(
                f"剔除規則指定的欄位 {key!r} 不在 CONFIG['columns'] 裡。\n"
                f"目前可用的語意欄：{sorted(k for k in rows[0] if k != 'qty')}\n"
                f"請用語意 key（不是位置、不是欄名）指定剔除欄。")
        hit = [r for r in rows if r[key] in values]
        n_qty = sum(r["qty"] for r in hit)
        hit_set = id_set(hit)
        rows = [r for r in rows if id(r) not in hit_set]
        if verbose:
            flag = "  ← 列數少但量體大，別忽略" if hit and n_qty / max(len(hit), 1) > 50 else ""
            print(f"  剔除 {note}：{len(hit)} 列 / {n_qty} 單位{flag}")

    # 期別排除
    excl = set(cfg["exclude_periods"])
    dropped = [r for r in rows if r["period"] in excl]
    rows = [r for r in rows if r["period"] not in excl]
    if verbose and dropped:
        print(f"  排除未結束期別 {sorted(excl)}：{len(dropped)} 列 / "
              f"{sum(r['qty'] for r in dropped)} 單位")
    return rows


def id_set(items):
    return {id(x) for x in items}


def _report_last_period(rows, cfg):
    """印出最後一期的量體，提醒確認完不完整。"""
    per = defaultdict(int)
    for r in rows:
        per[r["period"]] += r["qty"]
    if not per:
        return
    ks = sorted(per)
    last, prev = ks[-1], (ks[-2] if len(ks) > 1 else None)
    msg = f"  最後一期 {last}：{per[last]} 單位"
    if prev:
        ratio = per[last] / per[prev] if per[prev] else 0
        msg += f"（前期 {per[prev]}，比值 {ratio:.0%}）"
        if ratio < 0.7:
            msg += "  ⚠ 明顯偏低，確認是否為未結束的當期"
    print(msg)


# ─────────────────────────────────────────────────────────────
# 開工前必跑的自檢
# ─────────────────────────────────────────────────────────────

def check_operator_history(rows, verbose=True):
    """★ 檢查經營者欄是「當期歷史」還是「現況快照」。

    這條錯了**不會報錯**，只會讓你把前任的業績算進接手方的基期——
    實測顯示同一份資料可因此得出「+20%」或「+260%」兩個都自洽但相反的答案。

    回傳 dict: {據點名: {"companies": [...], "overlap": [重疊期別]}}
    """
    if not any(r.get("store_raw") for r in rows):
        if verbose:
            print("\n★ 經營者歷史自檢：**跳過**——這份資料沒有據點欄。")
            print("  → 門市層歸屬只能靠另一份含據點的檔；若那份只有粗粒度（如半年），")
            print("    交接斷層（模組 C）就填 ⬜，不可宣稱「無斷層」。")
        return {}

    by_store = defaultdict(lambda: defaultdict(set))
    for r in rows:
        if r["company"]:
            by_store[r["store_name"]][r["company"]].add(r["period"])

    multi = {s: c for s, c in by_store.items() if len(c) > 1}
    out = {}
    for store, comps in multi.items():
        periods = list(comps.values())
        overlap = set.intersection(*periods) if len(periods) > 1 else set()
        out[store] = {
            "companies": {c: (min(p), max(p)) for c, p in comps.items()},
            "overlap": sorted(overlap),
        }

    if verbose:
        print("\n★ 經營者歷史自檢")
        if not multi:
            print("  沒有任何據點出現在多家公司底下。")
            print("  ⚠ 若你知道有據點易主過，那這個欄位就是**現況快照**——")
            print("    它把歷史回填成現任經營者。必須另取事件時間軸重建歸屬。")
        else:
            for store, info in out.items():
                print(f"  {store}")
                for c, (lo, hi) in info["companies"].items():
                    print(f"     {c}  {lo} ~ {hi}")
                if info["overlap"]:
                    print(f"     ⚠ 重疊期別 {info['overlap']} → 交接不乾淨，先問資料端")
                else:
                    print("     ✓ 零重疊 → 欄位帶當期歷史，可直接用公司欄歸屬")
    return out


def check_unattributed(rows, periods_by_label, own_brand=None, cfg=CONFIG, verbose=True):
    """未歸屬據點的比例——**分期算**。

    全期比例會稀釋掉分析窗口內的真實缺口（實測：全期 6.3% vs 分期 10.2%）。

    periods_by_label: {"2025H1": [...期別...], "2026H1": [...]}
    """
    if not any(r.get("store_raw") for r in rows):
        if verbose:
            print("\n★ 未歸屬據點：**跳過**——這份資料沒有據點欄（不是 100% 未歸屬）。")
        return {}

    own = own_brand or cfg["own_brand"]
    ph = cfg["store_placeholders"]
    out = {}
    for label, periods in periods_by_label.items():
        d = [r for r in rows if r["period"] in periods and r["brand"] == own
             and r["store_raw"] not in ph]
        total = sum(r["qty"] for r in d)
        una = sum(r["qty"] for r in d if not r["store_raw"])
        out[label] = (una, total, una / total if total else 0)
    if verbose:
        print("\n★ 未歸屬據點（分期）")
        for label, (una, total, pct) in out.items():
            print(f"  {label}: {una}/{total} = {pct:.1%}")
    return out


def check_store_churn(rows, periods_by_label, verbose=True):
    """★ 期間內開店／關店掃描 —— 基期干擾。

    某據點在基期有量、當期歸零（或反之），會讓它所屬群組的成長率失真。
    實測：一家停業門市的 112 台，讓整個「其他加盟」群組看起來在衰退。
    """
    if not any(r.get("store_raw") for r in rows):
        if verbose:
            print("\n★ 據點增減掃描：**跳過**——這份資料沒有據點欄。")
        return {}

    labels = list(periods_by_label)
    if len(labels) < 2:
        return {}
    a, b = labels[0], labels[-1]
    qa, qb = defaultdict(int), defaultdict(int)
    for r in rows:
        if r["period"] in periods_by_label[a]:
            qa[r["store_name"]] += r["qty"]
        elif r["period"] in periods_by_label[b]:
            qb[r["store_name"]] += r["qty"]

    closed = {s: qa[s] for s in qa if qa[s] > 0 and qb.get(s, 0) == 0}
    opened = {s: qb[s] for s in qb if qb[s] > 0 and qa.get(s, 0) == 0}
    if verbose:
        print(f"\n★ 期間內據點增減（{a} → {b}）")
        if closed:
            print(f"  {a} 有量、{b} 歸零（關店／停業）：")
            for s, q in sorted(closed.items(), key=lambda x: -x[1])[:8]:
                print(f"     {s}  基期 {q} 單位")
            print("     → 這些量體要單獨列出，不可混進群組成長率")
        if opened:
            print(f"  {b} 才出現（新開）：")
            for s, q in sorted(opened.items(), key=lambda x: -x[1])[:8]:
                print(f"     {s}  當期 {q} 單位")
        if not closed and not opened:
            print("  無據點增減。")
    return {"closed": closed, "opened": opened}


# ─────────────────────────────────────────────────────────────
# 市占率
# ─────────────────────────────────────────────────────────────

def pooled_share(rows, periods, regions=None, subareas=None, own_brand=None, cfg=CONFIG):
    """區間彙總市占率。回傳 (share, own_qty, total_qty)。

    分母是**全品牌**——這是「市占率」；只算自家品牌的是「品牌內份額」，
    兩者不同，不可混用。
    """
    own = own_brand or cfg["own_brand"]
    d = rows
    if regions is not None:
        d = [r for r in d if r["region"] in regions]
    if subareas is not None:
        d = [r for r in d if r["subarea"] in subareas]
    d = [r for r in d if r["period"] in periods]
    o = sum(r["qty"] for r in d if r["brand"] == own)
    t = sum(r["qty"] for r in d)
    return (o / t if t else float("nan")), o, t


def share_delta(rows, periods_a, periods_b, **kw):
    """前後期市占率變化。**YoY% 與 pp 一定要一起回傳**——只報一個會誤判。

    回傳 dict: share_a / share_b / pp（絕對變化）/ yoy（相對變化）
    """
    sa, oa, ta = pooled_share(rows, periods_a, **kw)
    sb, ob, tb = pooled_share(rows, periods_b, **kw)
    return {
        "share_a": sa, "share_b": sb,
        "own_a": oa, "own_b": ob, "total_a": ta, "total_b": tb,
        "pp":  (sb - sa) * 100,
        "yoy": ((sb - sa) / sa * 100) if sa else float("nan"),
    }


def periods_range(year, start_month, end_month):
    """產生期別清單，如 periods_range(2025, 1, 6) → ['202501', ..., '202506']"""
    return [f"{year}{m:02d}" for m in range(start_month, end_month + 1)]


if __name__ == "__main__":
    rows = load()
    H = {"前期": periods_range(2025, 1, 6), "後期": periods_range(2026, 1, 6)}
    check_operator_history(rows)
    check_unattributed(rows, H)
    check_store_churn(rows, H)
