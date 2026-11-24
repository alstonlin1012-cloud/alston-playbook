#!/usr/bin/env python3
"""驗算三份 fixture 是否真的落在設計的分支上。不看設計意圖，只看資料。"""
import csv, os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(BASE, name, "reg.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def half(ym):
    return "25" if ym.startswith("2025") else "26"


def agg(rows, keyfn):
    d = defaultdict(lambda: {"25": 0, "26": 0})
    for r in rows:
        k = keyfn(r)
        if k is not None:
            d[k][half(r["ym"])] += int(r["qty"])
    return d


def yoy(a, b):
    return (b / a - 1) * 100 if a else float("nan")


def share_block(rows, title, geo_filter=None):
    """算某地理範圍的品牌市占。"""
    sel = [r for r in rows if geo_filter is None or geo_filter(r)]
    g = agg(sel, lambda r: "G" if r["brand"] == "GOGORO" else "other")
    tot25 = g["G"]["25"] + g["other"]["25"]
    tot26 = g["G"]["26"] + g["other"]["26"]
    if tot25 == 0 or g["other"]["25"] + g["other"]["26"] == 0:
        print(f"  {title}: 品牌 {g['G']['25']}→{g['G']['26']}  【無競品分母 → 市占算不出】")
        return None
    s25, s26 = g["G"]["25"] / tot25 * 100, g["G"]["26"] / tot26 * 100
    print(f"  {title}: 品牌 {g['G']['25']}→{g['G']['26']}  大盤 {tot25}→{tot26} ({yoy(tot25,tot26):+.1f}%)  "
          f"市占 {s25:.3f}%→{s26:.3f}%  YoY {yoy(s25,s26):+.1f}%  pp {s26-s25:+.3f}")
    return s26 - s25


def operator_footprint(rows, title):
    """經營者口徑版圖：當期實際經營的門市量體。"""
    d = agg([r for r in rows if r["brand"] == "GOGORO" and r["operator"]],
            lambda r: r["operator"])
    print(f"  {title} 版圖（經營者口徑）：")
    for op, v in sorted(d.items()):
        print(f"    {op}: {v['25']} → {v['26']}  ({yoy(v['25'], v['26']):+.1f}%)  "
              f"{'↓ 縮小' if v['26'] < v['25'] else '↑ 擴大'}")


def stores(rows, title):
    d = agg([r for r in rows if r["store"]], lambda r: r["store"])
    ops = defaultdict(set)
    for r in rows:
        if r["store"]:
            ops[r["store"]].add((half(r["ym"]), r["operator"]))
    print(f"  {title} 門市：")
    for s, v in sorted(d.items()):
        o25 = next((o for h, o in ops[s] if h == "25"), "-")
        o26 = next((o for h, o in ops[s] if h == "26"), "-")
        tag = "  ★易主" if o25 != o26 else ""
        print(f"    {s}: {v['25']}→{v['26']} ({yoy(v['25'],v['26']):+.1f}%)  {o25}→{o26}{tag}")


for name, city, hinterland in [
    ("case-acquirer-broken", "新北市", "板橋區"),
    ("case-handover-failed", "台南市", "東區"),
    ("case-no-denominator", "桃園市", "中壢區"),
]:
    rows = load(name)
    print(f"\n{'='*70}\n{name}\n{'='*70}")
    share_block(rows, f"縣市層（{city}）", lambda r: r["city"] == city)
    share_block(rows, f"腹地層（{hinterland}）",
                lambda r: r["city"] == city and r["area"] == hinterland)
    others = sorted({r["area"] for r in rows if r["city"] == city} - {hinterland})
    if others:
        share_block(rows, f"對照組（{'+'.join(others)}）",
                    lambda r: r["city"] == city and r["area"] in others)
    stores(rows, "")
    operator_footprint(rows, "")
