#!/usr/bin/env python3
"""驗算第二批 fixture 是否真的踩到設計的結構。只看資料，不看設計意圖。"""
import csv, os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(BASE, name, "reg.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def h(ym):
    return "25" if ym.startswith("2025") else "26"


def agg(rows, keyfn):
    d = defaultdict(lambda: {"25": 0, "26": 0})
    for r in rows:
        k = keyfn(r)
        if k is not None:
            d[k][h(r["ym"])] += int(r["qty"])
    return d


def yoy(a, b):
    return (b / a - 1) * 100 if a else float("nan")


def share(rows, title, filt):
    sel = [r for r in rows if filt(r)]
    g = agg(sel, lambda r: "G" if r["brand"] == "GOGORO" else "o")
    t25, t26 = g["G"]["25"] + g["o"]["25"], g["G"]["26"] + g["o"]["26"]
    if not t25 or not (g["o"]["25"] + g["o"]["26"]):
        print(f"  {title}: 品牌 {g['G']['25']}→{g['G']['26']}  【無競品分母】")
        return
    s25, s26 = g["G"]["25"] / t25 * 100, g["G"]["26"] / t26 * 100
    print(f"  {title}: 品牌 {g['G']['25']}→{g['G']['26']}  大盤 {t25}→{t26} ({yoy(t25,t26):+.1f}%)  "
          f"市占 {s25:.3f}%→{s26:.3f}%  YoY {yoy(s25,s26):+.1f}%  pp {s26-s25:+.3f}")


def stores(rows):
    d = agg([r for r in rows if r["store"]], lambda r: r["store"])
    meta = {}
    for r in rows:
        if r["store"]:
            meta.setdefault(r["store"], {})[h(r["ym"])] = (r["operator"], r["brand"], r["city"], r["area"])
    print("   門市：")
    for s, v in sorted(d.items()):
        o25, o26 = meta[s].get("25", ("-",))[0], meta[s].get("26", ("-",))[0]
        brand, city, area = meta[s]["26"][1], meta[s]["26"][2], meta[s]["26"][3]
        tag = "  ★易主" if o25 != o26 else ""
        print(f"    {s:12s} [{brand:6s} {city}{area}] {v['25']:5d}→{v['26']:5d} "
              f"({yoy(v['25'],v['26']):+7.1f}%)  {o25}→{o26}{tag}")


# ── 案例 6：兩口徑是否真的方向相反 ──
print("=" * 74)
print("case-cross-city  ── 檢查：縣市內口徑 vs 全部據點口徑 是否方向相反")
print("=" * 74)
rows = load("case-cross-city")
share(rows, "台中市（目標縣市）", lambda r: r["city"] == "台中市")
share(rows, "中區（腹地）      ", lambda r: r["city"] == "台中市" and r["area"] == "中區")
share(rows, "彰化市（縣市外）  ", lambda r: r["city"] == "彰化縣")
stores(rows)

for who, target_city, exclude in [("宏運（接手方）", "台中市", "中區A店"),
                                  ("直營（轉出方）", "台中市", "中區A店")]:
    sel = [r for r in rows if r["operator"] == who[:2] and r["store"] != exclude]
    within = agg([r for r in sel if r["city"] == target_city], lambda r: "x")["x"]
    allsc = agg(sel, lambda r: "x")["x"]
    print(f"   {who} 既有／保留店：")
    print(f"     縣市內口徑   {within['25']:5d}→{within['26']:5d}  ({yoy(within['25'],within['26']):+7.1f}%)")
    print(f"     全部據點口徑 {allsc['25']:5d}→{allsc['26']:5d}  ({yoy(allsc['25'],allsc['26']):+7.1f}%)")
    flag = "★★ 方向相反" if (within['26'] > within['25']) != (allsc['26'] > allsc['25']) else "同向"
    print(f"     → {flag}")

fp = agg([r for r in rows if r["operator"]], lambda r: r["operator"])
print("   版圖（經營者口徑）：")
for op, v in sorted(fp.items()):
    print(f"     {op}: {v['25']}→{v['26']} ({yoy(v['25'],v['26']):+.1f}%)")

# ── 案例 7：品牌與經營者是否真的相反 ──
print("\n" + "=" * 74)
print("case-acquirer-sells-rival  ── 檢查：品牌視角 vs 經營者視角 是否相反")
print("=" * 74)
rows = load("case-acquirer-sells-rival")
share(rows, "高雄市（縣市）    ", lambda r: r["city"] == "高雄市")
share(rows, "前鎮區（腹地）    ", lambda r: r["city"] == "高雄市" and r["area"] == "前鎮區")
share(rows, "三民區（對照）    ", lambda r: r["city"] == "高雄市" and r["area"] == "三民區")
stores(rows)

tai = [r for r in rows if r["operator"] == "泰昇"]
g = agg([r for r in tai if r["brand"] == "GOGORO"], lambda r: "x")["x"]
c = agg([r for r in tai if r["brand"] != "GOGORO"], lambda r: "x")["x"]
tot = agg(tai, lambda r: "x")["x"]
print("   泰昇（接手方）：")
print(f"     GOGORO 版圖   {g['25']:5d}→{g['26']:5d}  ({yoy(g['25'],g['26']):+7.1f}%)  ← 品牌視角")
print(f"     競品門市      {c['25']:5d}→{c['26']:5d}  ({yoy(c['25'],c['26']):+7.1f}%)")
print(f"     全事業總量    {tot['25']:5d}→{tot['26']:5d}  ({yoy(tot['25'],tot['26']):+7.1f}%)  ← 經營者視角")
opp = (g['26'] > g['25']) != (tot['26'] > tot['25'])
print(f"     → {'★★ 兩視角相反' if opp else '同向'}")
