#!/usr/bin/env python3
"""第三批 fixture：讓框架的欄位裝不下。

案例 8 多據點同時易主：兩家店同時轉給同一接手方，且在**不同行政區**，
          兩區表現**方向相反** → 框架的「腹地層」是單數欄位，裝不下兩個目標市場。

案例 9 中途再轉手：A 店 2025H1 直營 → 2025H2 甲 → 2026H1 乙。
          同期 YoY（H1 vs H1）會**完全跳過甲**；而基期取直營或取甲，
          會得到相反的故事（乙 −10% vs 乙 +50%）。
"""
import csv, os

BASE = os.path.dirname(os.path.abspath(__file__))
HDR = ["city", "area", "ym", "brand", "operator", "store", "qty"]
W = [0.180, 0.155, 0.170, 0.160, 0.168, 0.167]


def months(year, half):
    rng = range(1, 7) if half == 1 else range(7, 13)
    return [f"{year}{m:02d}" for m in rng]


def spread(total):
    out = [int(round(total * w)) for w in W]
    out[-1] += total - sum(out)
    return out


def emit(rows, city, area, brand, segs, operator="", store=""):
    """segs = [(months_list, total, operator_for_that_segment), ...]"""
    for ms, tot, op in segs:
        for ym, q in zip(ms, spread(tot)):
            rows.append([city, area, ym, brand, op if op is not None else operator, store, q])


def write(name, rows):
    d = os.path.join(BASE, name)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "reg.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HDR)
        w.writerows(rows)
    print(f"  {name}/reg.csv  ({len(rows)} 列)")


H25, H26 = months(2025, 1), months(2026, 1)

# ═════════ 案例 8：兩家店同時易主，分屬不同區，方向相反 ═════════
# 合鑫同時接下 東區A店 與 南區B店。
#   東區A：200→260，東區大盤持平 → 市占 ↑
#   南區B：300→150，南區大盤成長 → 市占 ↓↓
# 腹地層要判東區還是南區？兩個都是事件現場，而且結論相反。
r8 = []
emit(r8, "台南市", "東區", "GOGORO", [(H25, 200, "直營"), (H26, 260, "合鑫")], store="東區A店")
emit(r8, "台南市", "南區", "GOGORO", [(H25, 300, "直營"), (H26, 150, "合鑫")], store="南區B店")
emit(r8, "台南市", "南區", "GOGORO", [(H25, 150, "合鑫"), (H26, 210, "合鑫")], store="南區X店")  # 合鑫既有
emit(r8, "台南市", "北區", "GOGORO", [(H25, 250, "直營"), (H26, 430, "直營")], store="北區C店")  # 直營保留
emit(r8, "台南市", "東區", "競品", [(H25, 9800, None), (H26, 9740, None)])
emit(r8, "台南市", "南區", "競品", [(H25, 9550, None), (H26, 10640, None)])
emit(r8, "台南市", "北區", "競品", [(H25, 9750, None), (H26, 9570, None)])
emit(r8, "嘉義市", "_", "GOGORO", [(H25, 500, None), (H26, 530, None)])
emit(r8, "嘉義市", "_", "競品", [(H25, ticks := 14500, None), (H26, 15070, None)])
write("case-multi-store", r8)

# ═════════ 案例 9：中途再轉手（三個經營者，兩次移轉）═════════
# 桃園蘆竹A店：2025H1 直營 200 → 2025H2 甲 120（崩）→ 2026H1 乙 180
#   基期取 2025H1（直營）→ 乙 −10%   ← 同期 YoY 的答案
#   基期取 2025H2（甲）  → 乙 +50%   ← 「乙接手後改善了」
# 兩個都算得出來，故事完全相反。而且同期 YoY 會**整段跳過甲**。
r9 = []
H25b = months(2025, 2)
emit(r9, "桃園市", "蘆竹區", "GOGORO",
     [(H25, 200, "直營"), (H25b, 120, "甲興"), (H26, 180, "乙豐")], store="蘆竹A店")
emit(r9, "桃園市", "蘆竹區", "GOGORO",
     [(H25, 150, "乙豐"), (H25b, 160, "乙豐"), (H26, 200, "乙豐")], store="蘆竹B店")  # 乙既有
emit(r9, "桃園市", "龜山區", "GOGORO",
     [(H25, 180, "直營"), (H25b, 190, "直營"), (H26, 240, "直營")], store="龜山C店")  # 直營保留
emit(r9, "桃園市", "蘆竹區", "競品",
     [(H25, 9650, None), (H25b, 9720, None), (H26, 9620, None)])
emit(r9, "桃園市", "龜山區", "競品",
     [(H25, 9820, None), (H25b, 9810, None), (H26, 9760, None)])
emit(r9, "新竹市", "_", "GOGORO", [(H25, 400, None), (H25b, 410, None), (H26, 430, None)])
emit(r9, "新竹市", "_", "競品", [(H25, 9600, None), (H25b, 9590, None), (H26, 9570, None)])
write("case-re-handover", r9)

print("\n完成。")
