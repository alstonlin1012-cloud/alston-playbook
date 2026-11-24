#!/usr/bin/env python3
"""第二批 fixture：測「事件結構複雜化」，不是測判定分支。

案例 6 跨縣市：接手方在目標縣市外另有據點，且方向相反
              → 「縣市內口徑」與「全部據點口徑」給出**相反答案**
              框架寫了「兩個都報」，但沒說判定該用哪個。

案例 7 競品經銷商：接手方同時經營競品門市
              → 品牌視角與經營者視角**利益相反**
              框架的視角 3 預設兩者一致。
"""
import csv, os

BASE = os.path.dirname(os.path.abspath(__file__))
HDR = ["city", "area", "ym", "brand", "operator", "store", "qty"]
M25 = [f"2025{m:02d}" for m in range(1, 7)]
M26 = [f"2026{m:02d}" for m in range(1, 7)]
W = [0.180, 0.155, 0.170, 0.160, 0.168, 0.167]


def spread(total):
    out = [int(round(total * w)) for w in W]
    out[-1] += total - sum(out)
    return out


def emit(rows, city, area, t25, t26, brand, operator="", store=""):
    for ms, tot in ((M25, t25), (M26, t26)):
        for ym, q in zip(ms, spread(tot)):
            rows.append([city, area, ym, brand, operator, store, q])


def write(name, rows, handover=None):
    d = os.path.join(BASE, name)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "reg.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HDR)
        w.writerows(rows)
    if handover:                       # 2026 起改掛新經營者
        store_name, new_op = handover
        with open(p, encoding="utf-8") as f:
            rr = list(csv.reader(f))
        for row in rr[1:]:
            if row[5] == store_name and row[2].startswith("2026"):
                row[4] = new_op
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rr)
    print(f"  {name}/reg.csv  ({len(rows)} 列)")


# ══════════════ 案例 6：跨縣市，兩口徑方向相反 ══════════════
# 標的在台中市中區。接手方「宏運」的既有店分布在兩個縣市：
#   台中中區B店（縣市內）  200 → 300   ↑
#   彰化市X店（縣市外）    300 → 100   ↓  ← 只出現在「全部據點口徑」
# 縣市內口徑：+50.0%          全部據點口徑：500→400 = −20.0%
# **兩個口徑給出相反的答案**——這正是規則存在的理由，但框架沒說判定用哪個。
r6 = []
emit(r6, "台中市", "中區", 240, 260, "GOGORO", "直營", "中區A店")   # 標的
emit(r6, "台中市", "中區", 200, 300, "GOGORO", "宏運", "中區B店")   # 既有・縣市內
emit(r6, "彰化縣", "彰化市", 300, 100, "GOGORO", "宏運", "彰化X店")  # 既有・縣市外
emit(r6, "台中市", "西區", 180, 320, "GOGORO", "直營", "西區C店")   # 直營保留・縣市內
emit(r6, "彰化縣", "彰化市", 150, 260, "GOGORO", "直營", "彰化D店")  # 直營保留・縣市外
# 競品分母
emit(r6, "台中市", "中區", 9560, 10440, "競品")
emit(r6, "台中市", "西區", 5820, 6680, "競品")
emit(r6, "彰化縣", "彰化市", 9550, 9640, "競品")
emit(r6, "南投縣", "_", 400, 430, "GOGORO")
emit(r6, "南投縣", "_", 9600, 10070, "競品")
write("case-cross-city", r6, ("中區A店", "宏運"))

# ══════════════ 案例 7：接手方同時是競品經銷商 ══════════════
# 標的高雄前鎮A店，2025 直營 → 2026 泰昇。
# 泰昇**同時經營競品門市**（泰昇競品店，同在前鎮區）：競品量 800 → 1600。
# GOGORO 在前鎮的份額掉，泰昇自己的總生意卻大幅成長。
#   → 品牌視角：接手方讓品牌失血
#   → 經營者視角：泰昇賺得更多
# 框架的視角 3 預設兩者一致，本案讓它們**相反**。
r7 = []
emit(r7, "高雄市", "前鎮區", 300, 180, "GOGORO", "直營", "前鎮A店")     # 標的
emit(r7, "高雄市", "前鎮區", 200, 150, "GOGORO", "泰昇", "泰昇B店")     # 泰昇既有 GOGORO 店
emit(r7, "高雄市", "前鎮區",  800, 1600, "競品", "泰昇", "泰昇競品店")   # ★ 同一經營者的競品門市
emit(r7, "高雄市", "前鎮區", 8700, 8270, "競品")                        # 其他競品（無門市）
emit(r7, "高雄市", "三民區", 250, 400, "GOGORO", "直營", "三民C店")     # 直營保留
emit(r7, "高雄市", "三民區", 9750, 9600, "競品")
emit(r7, "台南市", "_", 900, 980, "GOGORO")
emit(r7, "台南市", "_", 29100, 30020, "競品")
write("case-acquirer-sells-rival", r7, ("前鎮A店", "泰昇"))

print("\n完成。")
