#!/usr/bin/env python3
"""產生三個未覆蓋分支的測試 fixture。

案例 3 接手方有問題：整體 ✅✅ ／ 轉出方 ✅ ／ 接手方 ❌（版圖縮小）
案例 4 易主失敗：      整體 ❌   ／ 接手方 ❌
案例 5 不下定調：      無競品資料 → 算不出市占 → 整體市場 ⬜
"""
import csv, os

BASE = os.path.dirname(os.path.abspath(__file__))
HDR = ["city", "area", "ym", "brand", "operator", "store", "qty"]
M25 = [f"2025{m:02d}" for m in range(1, 7)]
M26 = [f"2026{m:02d}" for m in range(1, 7)]

# 月度權重：讓半年總量分散到 6 個月，且不完全平均（避免看起來像假資料）
W = [0.180, 0.155, 0.170, 0.160, 0.168, 0.167]


def spread(total, weights=W):
    """把半年總量拆成 6 個月，確保加總完全等於 total。"""
    out = [int(round(total * w)) for w in weights]
    out[-1] += total - sum(out)
    return out


def emit(rows, city, area, total25, total26, brand, operator="", store=""):
    for ms, tot in ((M25, total25), (M26, total26)):
        for ym, q in zip(ms, spread(tot)):
            rows.append([city, area, ym, brand, operator, store, q])


def write(name, rows):
    d = os.path.join(BASE, name)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "reg.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HDR)
        w.writerows(rows)
    print(f"  {p}  ({len(rows)} 列)")


# ───────────────────────── 案例 3：接手方有問題 ─────────────────────────
# 新北市：板橋區（事件腹地）、三重區、中和區
# 標的＝板橋A店（直營→宇泰）。宇泰既有店＝三重X店、中和Y店，兩家都在崩。
# 關鍵：宇泰接了一家店，版圖卻還是縮小（500→430）——這是 ❌ 的唯一定義。
r3 = []
# GOGORO 門市
emit(r3, "新北市", "板橋區", 240, 200, "GOGORO", "直營", "板橋A店")   # 2025 直營
emit(r3, "新北市", "板橋區", 160, 500, "GOGORO", "直營", "板橋C店")   # 直營保留店
emit(r3, "新北市", "三重區", 300, 150, "GOGORO", "宇泰", "三重X店")   # 宇泰既有（崩）
emit(r3, "新北市", "三重區", 100, 450, "GOGORO", "直營", "三重D店")   # 直營保留店
emit(r3, "新北市", "中和區", 200,  80, "GOGORO", "宇泰", "中和Y店")   # 宇泰既有（崩）
# 競品（分母）
emit(r3, "新北市", "板橋區", 7600,  9300, "競品")
emit(r3, "新北市", "三重區", 5600,  6400, "競品")
emit(r3, "新北市", "中和區", 5800,  6820, "競品")
# 外縣市（基準層用）
emit(r3, "桃園市", "_", 900, 1000, "GOGORO")
emit(r3, "桃園市", "_", 29100, 31000, "競品")
emit(r3, "台中市", "_", 1200, 1260, "GOGORO")
emit(r3, "台中市", "_", 38800, 40740, "競品")
write("case-acquirer-broken", r3)

# 板橋A店 2026 起改掛宇泰 → 覆寫該店 2026 的 operator
p = os.path.join(BASE, "case-acquirer-broken", "reg.csv")
with open(p, encoding="utf-8") as f:
    rows = list(csv.reader(f))
for row in rows[1:]:
    if row[5] == "板橋A店" and row[2].startswith("2026"):
        row[4] = "宇泰"
with open(p, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)

# ───────────────────────── 案例 4：易主失敗 ─────────────────────────
# 台南市：東區（事件腹地）、南區
# 市場微幅成長，但品牌腹地份額崩、接手方版圖也縮 → ❌❌
r4 = []
# 版圖必須「含移轉後仍縮小」才是 ❌：弘昌 260 →（南區X 120 ＋ 接來的東區A 100）＝ 220
emit(r4, "台南市", "東區", 300, 100, "GOGORO", "直營", "東區A店")     # 標的，2026 起弘昌
emit(r4, "台南市", "東區", 100,  60, "GOGORO", "直營", "東區C店")     # 直營保留（也在退）
emit(r4, "台南市", "南區", 260, 120, "GOGORO", "弘昌", "南區X店")     # 弘昌既有（崩）
emit(r4, "台南市", "南區", 140, 130, "GOGORO", "直營", "南區D店")
emit(r4, "台南市", "東區", 9600, 10840, "競品")
emit(r4, "台南市", "南區", 9600, 10750, "競品")
emit(r4, "高雄市", "_", 1500, 1580, "GOGORO")
emit(r4, "高雄市", "_", 38500, 40420, "競品")
emit(r4, "嘉義市", "_", 400, 430, "GOGORO")
emit(r4, "嘉義市", "_", 9600, 10070, "競品")
write("case-handover-failed", r4)

p = os.path.join(BASE, "case-handover-failed", "reg.csv")
with open(p, encoding="utf-8") as f:
    rows = list(csv.reader(f))
for row in rows[1:]:
    if row[5] == "東區A店" and row[2].startswith("2026"):
        row[4] = "弘昌"
with open(p, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)

# ───────────────────────── 案例 5：不下定調（⬜）─────────────────────────
# 桃園市：中壢區（事件腹地）、平鎮區
# 只有自家品牌領牌資料，【完全沒有競品列】→ 算不出市占 → 整體市場 ⬜
# 陷阱：絕對量全面成長，很誘人拿來填 ✅
r5 = []
emit(r5, "桃園市", "中壢區", 200, 260, "GOGORO", "直營", "中壢A店")   # 標的，2026 起長勝
emit(r5, "桃園市", "中壢區", 150, 210, "GOGORO", "長勝", "中壢B店")   # 長勝既有
emit(r5, "桃園市", "平鎮區", 180, 240, "GOGORO", "直營", "平鎮C店")   # 直營保留
emit(r5, "桃園市", "平鎮區", 120, 170, "GOGORO", "直營", "平鎮D店")
write("case-no-denominator", r5)

p = os.path.join(BASE, "case-no-denominator", "reg.csv")
with open(p, encoding="utf-8") as f:
    rows = list(csv.reader(f))
for row in rows[1:]:
    if row[5] == "中壢A店" and row[2].startswith("2026"):
        row[4] = "長勝"
with open(p, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)

print("\n完成。")
