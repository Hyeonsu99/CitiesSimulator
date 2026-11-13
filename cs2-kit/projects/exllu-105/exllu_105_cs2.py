"""Tower 105: 50-floor Type C luxury tower on the OSM C-type outline, green-glass gabled crown,
round elevated helipad on the north wing, granite podium and portico.

Evidence:
  plan  OpenStreetMap way 934368148 (C outline shared by 105-108, 38.4 x 44.6 m, 1148 m2), overlaid on
        exllu-105/photos/dong_crops/grid.png: north wing carries the round helipad, west arm, main body south.
  crown photos/site.jpg (green glass gable crown between white gables), view_top_far_w.png (round helipad ring).
  base  photos/view_n_base.png, view_nw_base.png (105 numeral on the portico; louvres + windows on the entrance face).
Model axes: front (-Y) = north; +X = west; y = distance south of the north wing face.
"""
import math
import os
import sys

import numpy as np


def find_kit():
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        if os.path.exists(os.path.join(path, "cs2kit.py")):
            return path
        path = os.path.dirname(path)
    raise RuntimeError("cs2kit.py not found")


sys.path.insert(0, find_kit())
import cs2kit as K  # noqa: E402

# No _Gls glass mesh: avoids night z-fighting flicker verified in tower 103 tests.
DONG = "105"
ASSET = f"HighriseTower{DONG}"

W, D, FH, NF = 38.4, 44.6, 2.94, 50          # 50 floors, OSM C outline bounding box
GH = 5.24                                     # double-height lobby storey
H = GH + FH * (NF - 1)                        # 149.3 m roof slab; crown apex ~159 m
REF_F = 26                                    # refuge floor: louvre band instead of windows


def zf(f):
    """Floor level of storey f (0 = lobby)."""
    return 0.0 if f == 0 else GH + (f - 1) * FH


X = W / 2                                     # 19.2 m
LEDGE_P, LEDGE_T = 0.55, 0.28                 # per-floor balcony ledge projection / thickness
SILL, HEAD = 0.75, 2.45                       # standard window sill and head heights


def granite(ctx, cols, rows, darken, speck, polish=0.0):
    k = ctx.w / 256.0
    d = ctx.joints(cols=cols, rows=rows, width_m=0.010, depth=1.4, stagger=0.0, darken=darken, tone=5.0)
    ctx.grain(amp=speck * 0.9, scale_px=max(2, int(1.5 * k)), height=0.5, seed=3)
    ctx.rgb += ctx.noise(max(4, int(7 * k)), speck * 0.7, 3, seed=5)[..., None]
    ctx.rgb += ctx.noise(max(16, int(40 * k)), speck * 0.5, 2, seed=9)[..., None]
    ctx.stains(amount=0.05, scale_px=max(32, int(64 * k)), streaks=0.6, seed=2)
    ctx.gloss[...] = np.clip(ctx.gloss + polish + 0.06 * ctx.noise(max(8, int(20 * k)), 1.0, 2, seed=11), 0.05, 0.95)
    ctx.gloss[d > 0.2] = 0.15


def paving(ctx, n):
    ctx.joints(cols=n, rows=n, width_m=0.006, depth=1.0, darken=0.22, tone=3.0)
    ctx.grain(amp=3.0, scale_px=2, height=0.3, seed=4)
    ctx.rgb += ctx.noise(24, 3.0, 2, seed=6)[..., None]


def roofing(ctx):
    ctx.joints(cols=2, rows=2, width_m=0.02, depth=0.6, darken=0.12, tone=3.0)
    ctx.grain(amp=4.0, scale_px=2, height=0.4, seed=7)
    ctx.rgb += ctx.noise(48, 7.0, 3, seed=8)[..., None]
    ctx.stains(amount=0.10, scale_px=96, streaks=0.0, seed=12)


def shutter(ctx):
    mx, mz = ctx.meters()
    sl = (mz / 0.11) % 1.0
    ctx.rgb -= (np.clip(1.0 - sl / 0.22, 0, 1) * 46.0)[..., None]
    ctx.rgb += (np.clip((sl - 0.7) / 0.3, 0, 1) * 8.0)[..., None]
    ctx.height += sl * 0.8
    fr = (mx < 0.035) | (mx > ctx.tile[0] - 0.035) | (mz < 0.05) | (mz > ctx.tile[1] - 0.05)
    ctx.rgb[fr] = np.array([236, 237, 234], np.float32)
    ctx.height[fr] = 1.2


def clerestory(ctx):
    mx, mz = ctx.meters()
    ctx.rgb += (ctx.v * 26.0 - 6.0)[..., None]
    fr = (mx < 0.025) | (mx > ctx.tile[0] - 0.025) | (mz < 0.03) | (mz > ctx.tile[1] - 0.03)
    ctx.rgb[fr] = np.array([225, 227, 224], np.float32)
    ctx.gloss[...] = np.where(fr, 0.4, 0.9)
    ctx.emis[...] = np.where(fr, 0.0, 0.04)


VEST_W, VEST_H = 5.1, 2.75


def vestibule(ctx):
    x, z = ctx.u * VEST_W, ctx.v * VEST_H
    ctx.rgb[...] = np.array([46, 62, 66], np.float32)
    ctx.rgb += (ctx.v * 34.0)[..., None]
    ctx.rgb += (((x * 0.6 + z) % 1.7 < 0.10) * 16.0)[..., None]
    ctx.gloss[...] = 0.9
    ctx.emis[...] = 0.07 + 0.03 * (z < 2.1)
    steel = np.array([172, 176, 178], np.float32)
    fr = (x < 0.07) | (x > VEST_W - 0.07) | (z < 0.06) | (z > VEST_H - 0.07) | (np.abs(z - 2.15) < 0.035)
    for xm in (1.05, VEST_W - 1.05):
        fr |= np.abs(x - xm) < 0.035
    door = (x > 1.05) & (x < VEST_W - 1.05) & (z < 2.15)
    fr |= door & ((np.abs(x - VEST_W / 2) < 0.03) | (np.abs(x - 1.8) < 0.025) | (np.abs(x - (VEST_W - 1.8)) < 0.025))
    kick = door & (z < 0.28) & (np.abs(x - VEST_W / 2) < 0.75)
    pull = (np.abs(np.abs(x - VEST_W / 2) - 0.14) < 0.02) & (z > 0.85) & (z < 1.45)
    ctx.rgb[fr | kick] = steel
    ctx.rgb[pull] = np.array([214, 216, 216], np.float32)
    m = fr | kick | pull
    ctx.gloss[m] = 0.6
    ctx.emis[m] = 0.0
    ctx.height[m] = 1.0


def soffit(ctx):
    mx, mz = ctx.meters()
    edge = (mx < 0.012) | (mx > ctx.tile[0] - 0.012) | (mz < 0.012) | (mz > ctx.tile[1] - 0.012)
    ctx.rgb[edge] *= 0.72
    ctx.rgb += ctx.noise(16, 2.0, 2, seed=4)[..., None]
    d = np.hypot(mx - ctx.tile[0] / 2, mz - ctx.tile[1] / 2)
    ctx.emis[...] = 0.35 * np.clip(1.0 - (d / 0.075) ** 4, 0, 1) + 0.05 * np.exp(-(d / 0.35) ** 2)
    ctx.rgb[(d > 0.075) & (d < 0.10)] = np.array([120, 122, 122], np.float32)


def window_glass(ctx):
    g = K.REF_GRID
    units = max([w["unit"] for w in WS.items] + [0]) + 1
    stride = 7 if math.gcd(7, g * g) == 1 else 11
    count = {}
    for w in WS.items:
        k = ((w["floor"] * units + w["unit"]) * stride) % (g * g)
        count[k] = count.get(k, 0) + 1
    n = max(1, math.ceil(math.sqrt(max(list(count.values()) + [1]))))
    su, sv = ctx.u * g * n, ctx.v * g * n
    sid = (np.floor(sv).astype(np.int64) * g * n + np.floor(su).astype(np.int64))
    fu, fv = su % 1.0, sv % 1.0
    h = (sid * 2654435761) % 1000 / 1000.0
    h2, h3 = (h * 7) % 1.0, (h * 13) % 1.0
    ctx.rgb[...] = np.array([64, 106, 108], np.float32) + ((h - 0.5) * 18)[..., None]
    ctx.rgb += (fv * 46 - 6)[..., None]
    m = (fu * 0.7 + fv) % 1.0
    ctx.rgb += (((m > 0.30) & (m < 0.37)) * 20.0)[..., None]
    ctx.rgb += (((m > 0.62) & (m < 0.64)) * 12.0)[..., None]
    edge = np.minimum(np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv))
    ctx.rgb *= (0.72 + 0.28 * np.clip(edge / 0.035, 0, 1))[..., None]
    curt = h2 < 0.45
    cw = 0.10 + 0.08 * h3
    cmask = curt & ((fu < cw) | (fu > 1 - cw))
    fold = 0.82 + 0.18 * np.sin(fu * 90.0 + h * 40.0)
    cloth = np.array([204, 194, 174], np.float32) * fold[..., None]
    ctx.rgb[cmask] = ctx.rgb[cmask] * 0.3 + cloth[cmask] * 0.7
    blind = (~curt) & (h2 > 0.72) & (fv > 0.45 + 0.4 * h3)
    slat = 0.9 + 0.1 * np.sin(fv * 160.0)
    shade = np.array([214, 212, 204], np.float32) * slat[..., None]
    ctx.rgb[blind] = ctx.rgb[blind] * 0.25 + shade[blind] * 0.75

    lit = (np.floor(ctx.v * g).astype(np.int64) * g + np.floor(ctx.u * g).astype(np.int64)) < LIT_CELLS
    r = max(1, round(ctx.w * 0.008))
    m = np.pad(lit, r, constant_values=True)
    for ax in (0, 1):
        m = np.logical_and.reduce([np.roll(m, k, ax) for k in range(-r, r + 1)])
    lit = m[r:-r, r:-r]
    level = 0.6 + 0.4 * ((h * 29) % 1.0)
    glow = level * (0.75 + 0.25 * fv) * np.where(cmask | blind, 0.55, 1.0)
    ctx.emis[...] = np.where(lit, glow, 0.0)
    ctx.gloss[...] = np.where(cmask | blind, 0.25, 0.42)


def mesh_grid(ctx, n, w, col):
    m = ((ctx.u * n) % 1.0 < w) | ((ctx.v * n) % 1.0 < w)
    ctx.rgb[m] = np.array(col, np.float32)


def foliage(ctx):
    ctx.grain(amp=14.0, scale_px=2, height=0.6, seed=21)
    ctx.rgb += ctx.noise(8, 14.0, 3, seed=22)[..., None]
    ctx.rgb += ctx.noise(24, 6.0, 2, seed=23)[..., None]


def flat_emis(v):
    return lambda c: c.emis.__setitem__(Ellipsis, v)


def crown_glass(ctx):
    """Green glazed crown (site.jpg) with white mullions every 1.5 m and transoms every 2 m."""
    mx, mz = ctx.meters()
    ctx.rgb[...] = np.array([76, 146, 140], np.float32)
    ctx.rgb += (ctx.v * 32.0)[..., None]
    fr = ((mx % 1.5) < 0.055) | (mz < 0.05) | (mz > ctx.tile[1] - 0.05) | ((mz % 2.94) < 0.065)
    ctx.rgb[fr] = np.array([224, 229, 227], np.float32)
    ctx.gloss[...] = np.where(fr, 0.42, 0.92)
    ctx.emis[...] = np.where(fr, 0.0, 0.05)


# Pure-NumPy anti-aliased vector SDF typography for crisp signage without external font/PIL dependencies
_GLYPHS = {
    "E": ((0.15, 0.10, 0.15, 0.90), (0.15, 0.90, 0.85, 0.90), (0.15, 0.52, 0.72, 0.52), (0.15, 0.10, 0.85, 0.10)),
    "X": ((0.15, 0.10, 0.85, 0.90), (0.15, 0.90, 0.85, 0.10)),
    "L": ((0.22, 0.10, 0.22, 0.90), (0.22, 0.10, 0.82, 0.10)),
    "U": ((0.15, 0.90, 0.15, 0.28), (0.15, 0.28, 0.30, 0.10), (0.30, 0.10, 0.70, 0.10),
          (0.70, 0.10, 0.85, 0.28), (0.85, 0.28, 0.85, 0.90)),
    "T": ((0.10, 0.90, 0.90, 0.90), (0.50, 0.10, 0.50, 0.90)),
    "O": ((0.28, 0.10, 0.72, 0.10), (0.72, 0.10, 0.86, 0.28), (0.86, 0.28, 0.86, 0.72), (0.86, 0.72, 0.72, 0.90),
          (0.72, 0.90, 0.28, 0.90), (0.28, 0.90, 0.14, 0.72), (0.14, 0.72, 0.14, 0.28), (0.14, 0.28, 0.28, 0.10)),
    "W": ((0.08, 0.90, 0.26, 0.10), (0.26, 0.10, 0.50, 0.62), (0.50, 0.62, 0.74, 0.10), (0.74, 0.10, 0.92, 0.90)),
    "R": ((0.16, 0.10, 0.16, 0.90), (0.16, 0.90, 0.70, 0.90), (0.70, 0.90, 0.84, 0.78), (0.84, 0.78, 0.84, 0.58),
          (0.84, 0.58, 0.70, 0.48), (0.70, 0.48, 0.16, 0.48), (0.52, 0.48, 0.86, 0.10)),
    "0": ((0.28, 0.10, 0.72, 0.10), (0.72, 0.10, 0.86, 0.28), (0.86, 0.28, 0.86, 0.72), (0.86, 0.72, 0.72, 0.90),
          (0.72, 0.90, 0.28, 0.90), (0.28, 0.90, 0.14, 0.72), (0.14, 0.72, 0.14, 0.28), (0.14, 0.28, 0.28, 0.10)),
    "1": ((0.28, 0.74, 0.54, 0.90), (0.54, 0.90, 0.54, 0.10), (0.24, 0.10, 0.82, 0.10)),
    "5": ((0.82, 0.90, 0.20, 0.90), (0.20, 0.90, 0.18, 0.56), (0.18, 0.56, 0.68, 0.56), (0.68, 0.56, 0.84, 0.40),
          (0.84, 0.40, 0.84, 0.24), (0.84, 0.24, 0.68, 0.10), (0.68, 0.10, 0.20, 0.10)),
    "6": ((0.76, 0.90, 0.34, 0.90), (0.34, 0.90, 0.16, 0.70), (0.16, 0.70, 0.16, 0.26), (0.16, 0.26, 0.34, 0.10),
          (0.34, 0.10, 0.72, 0.10), (0.72, 0.10, 0.86, 0.26), (0.86, 0.26, 0.86, 0.42), (0.86, 0.42, 0.70, 0.54),
          (0.70, 0.54, 0.16, 0.54)),
    "7": ((0.14, 0.90, 0.86, 0.90), (0.86, 0.90, 0.42, 0.10)),
    "8": ((0.28, 0.52, 0.72, 0.52), (0.28, 0.10, 0.72, 0.10), (0.72, 0.10, 0.86, 0.24), (0.86, 0.24, 0.86, 0.38),
          (0.86, 0.38, 0.72, 0.52), (0.28, 0.52, 0.14, 0.38), (0.14, 0.38, 0.14, 0.24), (0.14, 0.24, 0.28, 0.10),
          (0.28, 0.52, 0.16, 0.64), (0.16, 0.64, 0.16, 0.78), (0.16, 0.78, 0.30, 0.90), (0.30, 0.90, 0.70, 0.90),
          (0.70, 0.90, 0.84, 0.78), (0.84, 0.78, 0.84, 0.64), (0.84, 0.64, 0.72, 0.52)),
}


def _sdf_segs(px, py, segs):
    d = np.full(px.shape, 1e6, np.float32)
    for x0, y0, x1, y1 in segs:
        vx, vy = x1 - x0, y1 - y0
        l2 = vx * vx + vy * vy + 1e-12
        t = np.clip(((px - x0) * vx + (py - y0) * vy) / l2, 0.0, 1.0)
        dist = np.hypot(px - (x0 + t * vx), py - (y0 + t * vy))
        d = np.minimum(d, dist)
    return d


def _exllu_segs(cx, cy, ch_w, ch_h):
    """Exact world-aspect strokes for EXLLU TOWER (twin skyscraper L spires + wide spaced TOWER)."""
    segs = []
    # Ref portico & crown wordmark: uppercase E X L L U with staggered architectural L spires + TOWER
    items = [("E", 1.0), ("X", 1.0), ("L", 1.44), ("L", 1.76), ("U", 1.0),
             (" ", 0.72), ("T", 0.90), ("O", 0.90), ("W", 0.98), ("E", 0.90), ("R", 0.90)]
    adv = ch_w * 1.18
    x_pos = cx - adv * 5.05
    for idx, (ch, hs) in enumerate(items):
        gw = ch_w * (0.82 if ch == "L" else (1.06 if ch == "W" else (0.92 if idx > 5 else 0.96)))
        gh = ch_h * hs
        if ch == "L":
            # Crisp skyscraper L spire + distinct horizontal L base foot so twin L's never read as "ll"
            segs.append((x_pos + 0.14 * gw, cy, x_pos + 0.14 * gw, cy + gh))
            segs.append((x_pos + 0.14 * gw, cy + gh, x_pos + 0.42 * gw, cy + gh * 0.91))
            segs.append((x_pos + 0.14 * gw, cy, x_pos + 0.80 * gw, cy))
        elif ch in _GLYPHS:
            for a0, b0, a1, b1 in _GLYPHS[ch]:
                segs.append((x_pos + a0 * gw, cy + (b0 - 0.10) * gh / 0.80,
                             x_pos + a1 * gw, cy + (b1 - 0.10) * gh / 0.80))
        x_pos += adv * (0.62 if ch == " " else (0.94 if ch == "L" else (0.92 if idx > 5 else 1.02)))
    return segs


def _num_segs(cx, cy, gw, gh, text):
    segs = []
    step = gw * 1.18
    x0 = cx - 0.5 * ((len(text) - 1) * step + gw)
    for k, ch in enumerate(text):
        ox = x0 + k * step
        for a0, b0, a1, b1 in _GLYPHS.get(ch, ()):
            segs.append((ox + a0 * gw, cy + (b0 - 0.10) * gh / 0.80,
                         ox + a1 * gw, cy + (b1 - 0.10) * gh / 0.80))
    return segs


def paint_ent_lintel(ctx, w_m=5.25, h_m=1.02):
    granite(ctx, 5, 2, 0.16, 4.0, 0.08)
    px, py = ctx.u * w_m, ctx.v * h_m
    segs = _exllu_segs(w_m * 0.52, h_m * 0.30, 0.18, 0.30)
    d = _sdf_segs(px, py, segs)
    ds = _sdf_segs(px - 0.015, py + 0.015, segs)
    shad = np.clip(1.0 - (ds - 0.024) / 0.014, 0.0, 1.0)
    fg = np.clip(1.0 - (d - 0.024) / 0.012, 0.0, 1.0)
    ctx.rgb[...] = ctx.rgb * (1.0 - 0.38 * shad[..., None])
    ctx.rgb[...] = ctx.rgb * (1.0 - fg[..., None]) + np.array([76, 66, 56], np.float32) * fg[..., None]
    ctx.height += fg * 1.4
    ctx.gloss[...] = np.where(fg > 0.3, 0.55, ctx.gloss)


def paint_pier_num(ctx, w_m=1.40, h_m=1.10, bg="pink"):
    if bg == "pink":
        granite(ctx, 2, 1, 0.18, 7.0, 0.15)
    else:
        granite(ctx, 1, 1, 0.28, 7.0, 0.15)
    px, py = ctx.u * w_m, ctx.v * h_m
    segs = _num_segs(w_m * 0.50, h_m * 0.32, 0.25, 0.40, DONG)
    d = _sdf_segs(px, py, segs)
    ds = _sdf_segs(px - 0.022, py + 0.022, segs)
    shad = np.clip(1.0 - (ds - 0.036) / 0.018, 0.0, 1.0)
    fg = np.clip(1.0 - (d - 0.036) / 0.014, 0.0, 1.0)
    ctx.rgb[...] = ctx.rgb * (1.0 - 0.52 * shad[..., None])
    ctx.rgb[...] = ctx.rgb * (1.0 - fg[..., None]) + np.array([218, 180, 74], np.float32) * fg[..., None]
    ctx.height += fg * 2.4
    ctx.gloss[...] = np.where(fg > 0.3, 0.88, ctx.gloss)


def paint_pier_course(ctx):
    ctx.joints(cols=1, rows=10, width_m=0.009, depth=1.5, stagger=0.0, darken=0.22, tone=7.0)
    ctx.grain(amp=6.0, scale_px=2, height=0.6, seed=13)
    ctx.rgb += ctx.noise(12, 4.0, 2, seed=17)[..., None]


def paint_stainless(ctx):
    ctx.rgb += ctx.noise(4, 5.0, 1, seed=31)[..., None]
    streak = (np.sin(ctx.v * 180.0) * 3.0 + np.sin(ctx.v * 410.0) * 2.0)[..., None]
    ctx.rgb += streak
    ctx.gloss[...] = 0.86


def paint_rev_glass(ctx):
    ctx.rgb += (ctx.v * 26.0 - 4.0)[..., None]
    spec = (np.exp(-((ctx.u - 0.32) / 0.10) ** 2) * 34.0)[..., None]
    ctx.rgb += spec
    ctx.gloss[...] = 0.92
    ctx.emis[...] = 0.08


def paint_crown_sign(ctx, w_m=11.40, h_m=3.78):
    px, py = ctx.u * w_m, ctx.v * h_m
    ctx.rgb[...] = np.array([76, 146, 140], np.float32) + (ctx.v * 32.0)[..., None]
    fr = ((px % 1.5) < 0.055) | (py < 0.05) | (py > h_m - 0.05) | ((py % 2.0) < 0.055)
    ctx.rgb[fr] = np.array([224, 229, 227], np.float32)
    segs = _exllu_segs(w_m * 0.50, h_m * 0.34, 0.62, 0.92)
    d = _sdf_segs(px, py, segs)
    ds = _sdf_segs(px - 0.05, py + 0.05, segs)
    shad = np.clip(1.0 - (ds - 0.085) / 0.045, 0.0, 1.0)
    fg = np.clip(1.0 - (d - 0.085) / 0.032, 0.0, 1.0)
    ctx.rgb[...] = ctx.rgb * (1.0 - 0.45 * shad[..., None])
    ctx.rgb[...] = ctx.rgb * (1.0 - fg[..., None]) + np.array([222, 186, 82], np.float32) * fg[..., None]
    ctx.height += fg * 2.0
    ctx.gloss[...] = np.where(fg > 0.3, 0.90, np.where(fr, 0.42, 0.92))
    ctx.emis[...] = np.where(fg > 0.3, 0.38, np.where(fr, 0.0, 0.08))


TEX = {
    "stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 4, 0.3, 7.0, 0.12)),
    "pale": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 3, 0.12, 2.5)),
    "cool_pale": dict(tile=(2.4, FH), px=256, painter=lambda c: granite(c, 2, 3, 0.14, 2.8)),
    "mid_grey": dict(tile=(2.4, FH), px=256, painter=lambda c: granite(c, 2, 3, 0.18, 3.6)),
    "dark_paint": dict(tile=(2.4, FH), px=256, painter=lambda c: granite(c, 2, 3, 0.24, 5.0)),
    "grey_stone": dict(tile=(2.4, FH), px=512, painter=lambda c: granite(c, 2, 4, 0.18, 4.0)),
    "window": dict(px=2048, painter=window_glass, emissive=(255, 205, 150)),
    "pier_pink": dict(tile=(1.4, 1.2), px=512, painter=lambda c: granite(c, 2, 1, 0.18, 7.0, 0.15)),
    "pier_course": dict(tile=(0.65, 1.2), px=256, painter=paint_pier_course),
    "pier_num": dict(tile=(1.40, 1.10), px=512, painter=lambda c: paint_pier_num(c, 1.40, 1.10, "pink")),
    "pier_side_num": dict(tile=(1.15, 1.10), px=256, painter=lambda c: paint_pier_num(c, 1.15, 1.10, "dark")),
    "ent_lintel": dict(tile=(5.25, 1.02), px=512, painter=paint_ent_lintel),
    "crown_sign": dict(px=512, painter=paint_crown_sign, emissive=(215, 255, 228)),
    "stainless": dict(tile=(1.0, 1.0), px=128, painter=paint_stainless),
    "rev_glass": dict(tile=(1.0, 1.0), px=128, painter=paint_rev_glass, emissive=(185, 230, 215)),
    "roof": dict(tile=(4.0, 4.0), px=512, painter=roofing),
    "canopy": dict(tile=(1.2, 1.2), px=256, painter=lambda c: paving(c, 2)),
    "louver": dict(tile=(0.6, 2.05), px=256, painter=shutter),
    "clerestory": dict(tile=(0.85, 0.64), px=128, painter=clerestory, emissive=(255, 232, 196)),
    "vestibule": dict(px=1024, painter=vestibule, emissive=(255, 226, 184)),
    "soffit": dict(tile=(1.2, 1.2), px=256, painter=soffit, emissive=(255, 226, 184)),
    "heli_net": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 4, 0.10, (178, 182, 184))),
    "grating": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 12, 0.25, (70, 72, 74))),
    "ent_light": dict(px=32, painter=flat_emis(0.25), emissive=(255, 226, 184)),
    "under_light": dict(px=32, painter=flat_emis(0.15), emissive=(255, 214, 160)),
    "heli_light": dict(px=32, painter=flat_emis(0.35), emissive=(110, 255, 140)),
    "heli_light_y": dict(px=32, painter=flat_emis(0.35), emissive=(255, 214, 90)),
    "obst_light": dict(px=32, painter=flat_emis(0.6), emissive=(255, 58, 40)),
    "foliage": dict(tile=(1.2, 1.2), px=64, painter=foliage),
    "crown_glass": dict(tile=(3.0, 4.0), px=512, painter=crown_glass, emissive=(210, 255, 230)),
}

A = K.Atlas(size=4096, pad=16)
for name, color, metal, gloss, px in (
        ("stone", (92, 92, 104), 0.0, 0.35, 128),          # view_n_base: lavender-grey granite podium
        ("stone_trim", (64, 66, 76), 0.0, 0.35, 64),
        ("crown_glass", (100, 165, 155), 0.4, 0.9, 128),
        ("crown_sign", (100, 165, 155), 0.35, 0.9, 512),
        ("deck_under", (62, 66, 70), 0.2, 0.35, 64),
        ("pale", (224, 222, 214), 0.0, 0.3, 128),
        ("cool_pale", (206, 212, 218), 0.0, 0.3, 256),
        ("mid_grey", (152, 154, 154), 0.0, 0.28, 256),
        ("dark_paint", (88, 90, 96), 0.0, 0.26, 256),
        ("crown_white", (232, 233, 230), 0.1, 0.4, 64),
        ("railing", (200, 203, 205), 0.6, 0.5, 64),
        ("stainless", (198, 202, 206), 0.9, 0.85, 128),
        ("rev_glass", (38, 58, 62), 0.15, 0.92, 128),
        ("frame", (236, 237, 235), 0.3, 0.5, 64),
        ("louver", (230, 231, 229), 0.2, 0.4, 64),
        ("roof", (120, 122, 122), 0.0, 0.3, 64),
        ("heli_green", (74, 140, 104), 0.0, 0.25, 64),
        ("heli_white", (232, 234, 226), 0.0, 0.25, 64),
        ("pier_pink", (184, 150, 142), 0.0, 0.4, 512),
        ("pier_course", (190, 168, 158), 0.0, 0.35, 256),
        ("pier_num", (184, 150, 142), 0.0, 0.45, 512),
        ("pier_side_num", (92, 92, 104), 0.0, 0.45, 256),
        ("ent_lintel", (198, 182, 160), 0.0, 0.32, 512),
        ("canopy", (160, 163, 162), 0.2, 0.45, 128),
        ("grey_stone", (168, 168, 164), 0.0, 0.3, 512),
        ("heli_net", (72, 76, 80), 0.6, 0.4, 64),
        ("grating", (128, 132, 134), 0.6, 0.35, 64),
        ("heli_light", (90, 230, 120), 0.0, 0.6, 32),
        ("clerestory", (44, 58, 66), 0.5, 0.9, 128),
        ("vestibule", (46, 62, 66), 0.3, 0.9, 1024),
        ("soffit", (206, 208, 204), 0.0, 0.3, 256),
        ("ent_light", (250, 240, 220), 0.0, 0.6, 32),
        ("under_light", (250, 236, 210), 0.0, 0.6, 32),
        ("heli_light_y", (240, 208, 96), 0.0, 0.6, 32),
        ("obst_light", (226, 62, 50), 0.0, 0.6, 32),
        ("windsock", (236, 112, 44), 0.0, 0.2, 32),
        ("soil", (62, 50, 40), 0.0, 0.1, 64),
        ("foliage", (48, 76, 44), 0.0, 0.12, 64),
        ("window", (70, 110, 110), 0.0, 0.9, 1024)):
    A.add(name, color=color, ctrl=(0, 0, 0), metal=metal, gloss=gloss, **dict(dict(px=px), **TEX.get(name, {})))

WS = K.WindowSet()
LIT_CELLS = 7


def window(mb, stage, axis, c, s, a0, a1, z0, z1, floor, unit, mull=(0.38,), jambs=(True, True)):
    if floor == REF_F:
        louver(mb, stage, axis, c, s, a0, a1, z0 - 0.35, z1)
        return
    if stage == 0:
        cell = (((floor * 7919 + unit * 104729 + 12345) * 2654435761 & 0xFFFFFFFF) >> 16) % 25
        WS.add_face(axis, c, s, a0, a1, z0, z1, floor=floor, unit=cell * 18 % 25)
        if jambs[0]:
            K.axbox(mb, axis, c, s, a0 - 0.1, a0, 0, 0.12, z0, z1, "frame", skip=("top", "bottom"))
        if jambs[1]:
            K.axbox(mb, axis, c, s, a1, a1 + 0.1, 0, 0.12, z0, z1, "frame", skip=("top", "bottom"))
        e0, e1 = (0.1 if jambs[0] else 0.0), (0.1 if jambs[1] else 0.0)
        K.axbox(mb, axis, c, s, a0 - e0, a1 + e1, 0, 0.12, z1, z1 + 0.1, "frame")
        K.axbox(mb, axis, c, s, a0 - (0.15 if jambs[0] else 0.0), a1 + (0.15 if jambs[1] else 0.0),
                0, 0.18, z0 - 0.1, z0, "frame")
        lm = 3
        for u in mull:
            a = a0 + (a1 - a0) * u
            K.paint(mb, axis, c, s, a - 0.03, a + 0.03, z0, z1, "frame", layer=lm)
        zt = z0 + 0.55 * (z1 - z0)
        K.paint(mb, axis, c, s, a0, a1, zt, zt + 0.05, "frame", layer=lm + 1)


def louver(mb, stage, axis, c, s, a0, a1, z0, z1):
    if stage == 0:
        K.axbox(mb, axis, c, s, a0, a1, 0, 0.08, z0, z1, "louver")


WIDE = (0.1, 0.4, 0.46, 0.54, 0.6, 0.9)
PAIR = (0.18, 0.46, 0.54, 0.82)
QUAD = (0.22, 0.47, 0.53, 0.78)            # centre mullion pair: a single 0.5 bar trips the window-ray check
COMM6 = (0.16, 0.33, 0.47, 0.53, 0.67, 0.84)
HALF = (0.47, 0.53)
CW = 0.15

PALE_F = 4                                    # standard wings switch from dark granite podium after 4F
PORTICO_PALE_F = 5                            # projecting entrance block (WALLS 5..8) keeps granite through 5F
CROWN_F0 = 46                                 # top 4 residential floors (46..49) in South center merge into glass crown
CELL = 5.2                                    # window bay pitch (large units; keeps main < 95k tris)
LEDGE_P, LEDGE_T = 0.55, 0.28                 # per-floor balcony ledge on the south / west faces (view_w_full.png)

# ------------------------------------------------------------------------------
# PLAN: OSM way 934368148 in (u = west, v = south) metres, orthogonalised to +-0.3 m.  x = u - 19.2, y = v.
# North wing (helipad) u 0..16.4 / v 0..15.4; main body u 1.6..29.8 / v 15.4..44.6; west arm u 29.8..38.4 / v 14.4..24.6.
# ------------------------------------------------------------------------------
_UV = ((0, 0), (15, 0), (15, 5.7), (16.4, 5.7), (16.4, 15.4), (29.8, 15.4), (29.8, 14.4), (38.4, 14.4),
       (38.4, 24.6), (29.2, 24.6), (29.2, 26.8), (28, 26.8), (28, 34.9), (29.8, 34.9), (29.8, 44.6),
       (0, 44.6), (0, 34.9), (1.6, 34.9), (1.6, 15.4), (0, 15.4))
OUTLINE = [(round(u - X, 3), float(v)) for u, v in _UV]   # counter-clockwise seen from above
_RECTS_UV = ((0, 15, 0, 5.7), (0, 16.4, 5.7, 15.4), (29.8, 38.4, 14.4, 15.4), (1.6, 38.4, 15.4, 24.6),
             (1.6, 29.2, 24.6, 26.8), (1.6, 28, 26.8, 34.9), (0, 29.8, 34.9, 44.6))
ROOF_RECTS = [(round(u0 - X, 3), round(u1 - X, 3), v0, v1) for u0, u1, v0, v1 in _RECTS_UV]
ENT_Y = 14.4                                   # entrance face: west arm north wall; pink pier at its west corner (x 19.2)
# Verified multi-wall window & louver rhythm (exllu-106 entrance/hi, exllu-108 tower, view_ne/nw_hi)
WALL_SPANS = {
    ("y", 0.0, -19.2): ((-18.1, -14.9, WIDE), (-12.5, -10.1, PAIR), (-9.0, -5.6, WIDE)),
    ("x", -2.8, 5.7): ((12.2, 14.0, HALF),),                         # single stairwell bay on north court wall
    ("y", 14.4, 10.6): ((13.0, 14.2, ()), (15.3, 18.1, HALF)),
    ("y", 15.4, -2.8): ((-0.3, 5.5, QUAD), (7.7, 10.3, HALF)),
    ("x", 19.2, 14.4): ((15.5, 18.3, WIDE), (20.2, 23.0, PAIR)),
    ("x", 8.8, 26.8): ((28.0, 30.2, PAIR), (31.6, 33.8, PAIR)),
    ("x", 10.6, 34.9): ((36.0, 39.2, WIDE), (40.8, 43.4, PAIR)),
    ("y", 44.6, -19.2): (
        (-18.2, -14.8, WIDE), (-12.4, -8.8, WIDE),
        (-6.1, -2.3, QUAD), (-0.8, 1.8, HALF), (2.2, 4.4, PAIR),
        (5.9, 9.1, WIDE),
    ),
    ("x", -19.2, 0.0): ((1.0, 4.2, WIDE), (6.0, 8.6, PAIR), (10.4, 14.0, WIDE)),
}
ADJ_LOUVRES = (
    ("y", 15.4, -1, 5.75, 7.05),
    ("y", 0.0, -1, -14.65, -13.70),
    ("x", 19.2, 1, 18.55, 19.45),
    ("x", 10.6, 1, 39.45, 40.25),
    ("y", 44.6, 1, -14.55, -13.70),
    ("y", 44.6, 1, -8.55, -7.75),
    ("y", 44.6, 1, 9.35, 10.15),
    ("x", -19.2, -1, 4.40, 5.25),
)
# Back Wall 14 horizontal range replaced by vertical crown curtainwall on f >= CROWN_F0
CROWN_X0, CROWN_X1 = -7.2, 5.2


def _walls():
    out = []
    n = len(OUTLINE)
    for i in range(n):
        (ax, ay), (bx, by) = OUTLINE[i], OUTLINE[(i + 1) % n]
        if ay == by:
            axis, c, s, a0, a1 = "y", ay, (-1 if bx > ax else 1), min(ax, bx), max(ax, bx)
        else:
            axis, c, s, a0, a1 = "x", ax, (1 if by > ay else -1), min(ay, by), max(ay, by)
        out.append((axis, c, s, a0, a1, "win" if a1 - a0 >= 2.6 else "wall", "pale"))
    return tuple(out)


WALLS = _walls()


def bays(a0, a1):
    """Window spans for one wall segment: alternating wide / pair bays centred in CELL-wide cells."""
    L = a1 - a0
    if L < 2.6:
        return []
    n = max(1, int(L / CELL))
    m = a0 + (L - n * CELL) / 2
    out = []
    for i in range(n):
        c = m + (i + 0.5) * CELL
        w = min(3.2 if i % 2 == 0 else 2.4, L - 0.7)
        out.append((max(c - w / 2, a0 + 0.35), min(c + w / 2, a1 - 0.35), WIDE if w > 2.8 else PAIR))
    return out


def facade_floor(mb, stage, f, skip=None):
    """Windows of storey f on every outline wall; skip=(a0, a1) keeps the portico span of the entrance wall free."""
    z = zf(f)
    z0, z1 = (0.4, GH - 0.6) if f == 0 else (z + SILL, z + HEAD)
    u = 0
    for axis, c, s, a0, a1, kind, _ in WALLS:
        if kind != "win":
            continue
        if f == 0 and axis == "y" and c == 15.4 and a0 == -2.8:
            # 105/106/108 photo: 1F left of portico has 2 horizontal mechanical louvers behind the ramp + landing window
            louver(mb, stage, axis, c, s, 0.4, 3.0, 1.75, 3.15)
            louver(mb, stage, axis, c, s, 3.6, 6.2, 1.75, 3.15)
            window(mb, stage, axis, c, s, 7.7, 10.1, 1.15, 3.4, f, u, HALF)
            u += 1
            continue
        if f == 0 and axis == "x" and c == 19.2 and a0 == 14.4:
            # 105 side photo: deeply recessed wide 6-bay horizontal community window + dark granite surround & safety bar
            window(mb, stage, axis, c, s, 16.4, 23.8, 0.90, 3.55, f, u, COMM6)
            if stage < 2:
                mb.box(c, c + 0.32, 16.02, 24.18, 0.55, 0.78, "stone_trim", skip=("left",))
                mb.box(c, c + 0.32, 16.02, 24.18, 3.67, 3.98, "stone_trim", skip=("left",))
                mb.box(c, c + 0.32, 16.02, 16.24, 0.78, 3.67, "stone_trim", skip=("left", "bottom", "top"))
                mb.box(c, c + 0.32, 23.96, 24.18, 0.78, 3.67, "stone_trim", skip=("left", "bottom", "top"))
                if stage == 0:
                    prism(mb, (c + 0.16, 16.32, 1.40), (c + 0.16, 23.88, 1.40), 0.04, "railing")
            u += 1
            continue
        for b0, b1, mull in WALL_SPANS.get((axis, c, a0)) or bays(a0, a1):
            if skip and axis == "y" and c == ENT_Y and s < 0 and b1 > skip[0] and b0 < skip[1]:
                continue
            if f >= CROWN_F0 and axis == "y" and c == 44.6 and b1 > CROWN_X0 and b0 < CROWN_X1:
                continue
            window(mb, stage, axis, c, s, b0, b1, z0, z1, f, u, mull)
            u += 1
    if f > 0:
        for axis, c, s, a0, a1 in ADJ_LOUVRES:
            if f >= CROWN_F0 and axis == "y" and c == 44.6 and a1 > CROWN_X0 and a0 < CROWN_X1:
                continue
            louver(mb, stage, axis, c, s, a0, a1, z + 0.4, z1)


def _zone_mat(f):
    if f < PALE_F:
        return "grey_stone"
    if f < 10:
        return "cool_pale"
    if (10 <= f < 14) or (36 <= f < 40):
        return "mid_grey"
    return "pale"


def ledges(mb):
    """Per-floor balcony ledges on SW/south residential wings (flush center core on Wall 14 omitted)."""
    for axis, c, s, a0, a1, kind, _ in WALLS:
        if kind != "win" or s < 0 or a1 - a0 < 4.0:
            continue
        if not ((axis == "y" and c == 44.6) or (axis == "x" and a0 >= 26.8)):
            continue
        spans = ((a0 + 0.1, CROWN_X0 - 0.1), (CROWN_X1 + 0.1, a1 - 0.1)) if (axis == "y" and c == 44.6) else ((a0 + 0.1, a1 - 0.1),)
        for f in range(1, NF):
            z = zf(f)
            mat = _zone_mat(f)
            for s0, s1 in spans:
                K.axbox(mb, axis, c, s, s0, s1, 0, LEDGE_P, z, z + LEDGE_T, mat,
                        skip=("front",) if axis == "y" else ("left",))   # world face names: drop only the wall side


def ring(mb, cx, cy, r0, z0, r1, z1, region, n, flip=False, rot=0.0):
    """Band of n quads between polygon (r0, z0) and polygon (r1, z1)."""
    for i in range(n):
        a, b = rot + 2 * math.pi * i / n, rot + 2 * math.pi * (i + 1) / n
        q = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0), (cx + r0 * math.cos(b), cy + r0 * math.sin(b), z0),
             (cx + r1 * math.cos(b), cy + r1 * math.sin(b), z1), (cx + r1 * math.cos(a), cy + r1 * math.sin(a), z1)]
        mb.quad(q[::-1] if flip else q, A.uv(region), region)   # trapezoids: tiled rect() would overlap tiles


def prism(mb, p0, p1, w, region):
    d = [b - a for a, b in zip(p0, p1)]
    L = math.sqrt(sum(v * v for v in d))
    if L < 1e-6:
        return
    t = [v / L for v in d]
    u = [t[1], -t[0], 0.0]
    n = math.hypot(u[0], u[1]) or 1.0
    u = [v / n * w / 2 for v in u]
    v = [t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0]]
    vn = math.sqrt(sum(c * c for c in v)) or 1.0
    v = [c / vn * w / 2 for c in v]
    corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    for i in range(4):
        (a1, b1), (a2, b2) = corners[i], corners[(i + 1) % 4]
        off1 = [a1 * u[k] + b1 * v[k] for k in range(3)]
        off2 = [a2 * u[k] + b2 * v[k] for k in range(3)]
        q = [tuple(p0[k] + off1[k] for k in range(3)), tuple(p0[k] + off2[k] for k in range(3)),
             tuple(p1[k] + off2[k] for k in range(3)), tuple(p1[k] + off1[k] for k in range(3))]
        mb.rect(q, region)


# ==============================================================================
# ROOF: mitred parapet ring, green-glass gabled crown on the main body, round helipad on the north wing
# ==============================================================================
PT = 0.35
PH = H + 1.4


def parapet_ring(mb):
    P = OUTLINE
    n = len(P)

    def inward(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        return -dy / L, dx / L

    Q = []
    for i in range(n):
        n0, n1 = inward(P[i - 1], P[i]), inward(P[i], P[(i + 1) % n])
        Q.append((P[i][0] + (n0[0] + n1[0]) * PT, P[i][1] + (n0[1] + n1[1]) * PT))
    uv = A.uv("crown_white")
    for i in range(n):
        j = (i + 1) % n
        (ax, ay), (bx, by), (cx, cy), (dx, dy) = P[i], P[j], Q[j], Q[i]
        if i == 14:
            # Leave Wall 14 center (CROWN_X0..CROWN_X1) open so the glazed crown rises seamlessly above H
            for ox0, ox1, ix0, ix1 in ((ax, CROWN_X1, CROWN_X1, dx), (CROWN_X0, bx, cx, CROWN_X0)):
                mb.rect([(ox0, ay, H), (ox1, by, H), (ox1, by, PH), (ox0, ay, PH)], "pale")
                mb.rect([(ix0, cy, H), (ix1, dy, H), (ix1, dy, PH), (ix0, cy, PH)], "pale")
                mb.quad([(ox0, ay, PH), (ox1, by, PH), (ix0, cy, PH), (ix1, dy, PH)], uv, "crown_white")
            mb.rect([(CROWN_X1, ay, H), (CROWN_X1, cy, H), (CROWN_X1, cy, PH), (CROWN_X1, ay, PH)], "pale")
            mb.rect([(CROWN_X0, dy, H), (CROWN_X0, by, H), (CROWN_X0, by, PH), (CROWN_X0, dy, PH)], "pale")
            continue
        mb.rect([(ax, ay, H), (bx, by, H), (bx, by, PH), (ax, ay, PH)], "pale")
        mb.rect([(cx, cy, H), (dx, dy, H), (dx, dy, PH), (cx, cy, PH)], "pale")
        mb.quad([(ax, ay, PH), (bx, by, PH), (cx, cy, PH), (dx, dy, PH)], uv, "crown_white")


# South-center glazed crown flush with Wall 14 (y=44.6), merging top 4 floors into pitched gable (site.jpg / 108_tower)
CX0, CX1, CY0, CY1 = CROWN_X0, CROWN_X1, 31.6, 44.6
CZ0, CZE, CZA = H, H + 4.0, H + 9.4                      # parapet top, eaves, apex


def _gable_ear(mb, x0, x1, y0, ym, y1, z0, ze, za, region="crown_white"):
    """Closed solid pentagonal gable wall (no protruding rectangular corners past the sloped roof)."""
    # Two contiguous closed trapezoids meeting cleanly along y=ym
    for ya, yb, zta, ztb in ((y0, ym, ze, za), (ym, y1, za, ze)):
        q_l = [(x0, ya, z0), (x0, yb, z0), (x0, yb, ztb), (x0, ya, zta)][::-1]   # -X outward
        q_r = [(x1, ya, z0), (x1, yb, z0), (x1, yb, ztb), (x1, ya, zta)]         # +X outward
        q_t = [(x0, ya, zta), (x1, ya, zta), (x1, yb, ztb), (x0, yb, ztb)]       # sloped top (+Z)
        mb.rect(q_l, region)
        mb.rect(q_r, region)
        mb.rect(q_t, region)
    # Front (y0, -Y), back (y1, +Y) vertical gable ends
    mb.rect([(x0, y0, z0), (x1, y0, z0), (x1, y0, ze), (x0, y0, ze)], region)
    mb.rect([(x1, y1, z0), (x0, y1, z0), (x0, y1, ze), (x1, y1, ze)], region)


def _sloped_slab(mb, x0, x1, ya, za, yb, zb, th, mat_top, mat_bot, mat_edge):
    """Closed sloped roof panel of vertical thickness th between y=ya(za) and y=yb(zb)."""
    # top surface normal upward (+Z component), bottom normal downward
    flip = yb < ya
    top = [(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)]
    bot = [(x0, ya, za - th), (x1, ya, za - th), (x1, yb, zb - th), (x0, yb, zb - th)]
    mb.rect(top[::-1] if flip else top, mat_top)
    mb.rect(bot if flip else bot[::-1], mat_bot)
    # outer eaves/ridge faces along ya (-Y/+Y) and yb
    ey0 = [(x0, ya, za - th), (x1, ya, za - th), (x1, ya, za), (x0, ya, za)]
    ey1 = [(x0, yb, zb - th), (x1, yb, zb - th), (x1, yb, zb), (x0, yb, zb)]
    mb.rect(ey0[::-1] if flip else ey0, mat_edge)
    mb.rect(ey1 if flip else ey1[::-1], mat_edge)


def crown(mb, stage):
    ym = (CY0 + CY1) / 2
    if stage == 2:
        # Lightweight closed gable massing for LOD2
        _gable_ear(mb, CX0, CX1, CY0, ym, CY1, CZ0, CZE, CZA, "crown_glass")
        return
    ew = 0.50
    _gable_ear(mb, CX0, CX0 + ew, CY0, ym, CY1, CZ0, CZE, CZA + 0.35, "crown_white")
    _gable_ear(mb, CX1 - ew, CX1, CY0, ym, CY1, CZ0, CZE, CZA + 0.35, "crown_white")
    # Solid glass slopes between the gable ears (closed underside soffit + eaves fascia)
    _sloped_slab(mb, CX0 + ew, CX1 - ew, CY0 - 0.1, CZE, ym, CZA, 0.22, "crown_glass", "soffit", "crown_white")
    _sloped_slab(mb, CX0 + ew, CX1 - ew, CY1 + 0.1, CZE, ym, CZA, 0.22, "crown_glass", "soffit", "crown_white")
    # Rear (north) curtainwall + parapet plinth
    mb.box(CX0 + ew, CX1 - ew, CY0, CY0 + 0.30, H, H + 0.45, "pale", skip=("bottom",))
    mb.box(CX0 + ew, CX1 - ew, CY0 + 0.05, CY0 + 0.28, H + 0.45, CZE - 0.22, "crown_glass", skip=("bottom", "top"))
    # Front (south, y=CY1=44.6) glazed curtainwall fascia with EXLLU TOWER signage (flush continuation from zf(46))
    mb.box(CX0 + ew, CX1 - ew, CY1 - 0.28, CY1, H, CZE - 0.22, "crown_glass", skip=("bottom", "top", "back"))
    mb.quad(K.face_pts("y", CY1, 1, CX0 + ew, CX1 - ew, H, CZE - 0.22), A.uv_full("crown_sign"), "crown_sign")
    mb.box(CX0 + ew, CX1 - ew, ym - 0.2, ym + 0.2, CZA - 0.12, CZA + 0.18, "crown_white")
    if stage == 0:
        for x in (CX0 + ew / 2, CX1 - ew / 2):
            mb.box(x - 0.12, x + 0.12, ym - 0.12, ym + 0.12, CZA + 0.35, CZA + 0.68, "obst_light", skip=("bottom",))


# Round elevated helipad over the north wing (aerial: ~17 m deck with a net ring)  # estimated
HX, HY = 8.0 - X, 7.7
RDK, RG, HCORE, HNET = 7.6, 6.5, 1.3, 0.72      # net 0.72 m -> min x = -19.52 (inside 40 m lot)
HZ0, HZ1, HZT = H + 3.0, H + 5.4, H + 6.0        # taller core clearance under V-struts (roof_view_top_far_w)


def helipad(mb, stage):
    n = (32, 24, 10)[stage]
    ring(mb, HX, HY, HCORE, H, HCORE, HZ0, "crown_white", n)              # core column
    ring(mb, HX, HY, HCORE, HZ0, RDK, HZ1, "deck_under", n)               # conical underside
    ring(mb, HX, HY, RDK, HZ1, RDK, HZT, "crown_white", n)                # deck edge
    ring(mb, HX, HY, RDK, HZT, RG, HZT, "pale", n)                        # deck rim
    ring(mb, HX, HY, RG, HZT, 0.05, HZT, "heli_green", n)                 # green pad
    if stage == 2:
        return
    # Core collar where struts fan out
    zc0, zc1 = H + 0.8, H + 1.4
    ring(mb, HX, HY, HCORE + 0.16, zc0, HCORE + 0.16, zc1, "crown_white", n)
    ring(mb, HX, HY, HCORE + 0.16, zc1, HCORE, zc1, "crown_white", n)
    ring(mb, HX, HY, HCORE + 0.16, zc0, HCORE, zc0, "crown_white", n, flip=True)
    zt = HZT + 0.03
    for x0, x1, y0, y1 in ((-4.3, -4.15, -4.3, 4.3), (4.15, 4.3, -4.3, 4.3), (-4.15, 4.15, -4.3, -4.15),
                           (-4.15, 4.15, 4.15, 4.3), (-1.2, -0.95, -1.6, 1.6), (0.95, 1.2, -1.6, 1.6),
                           (-0.95, 0.95, -0.12, 0.12)):
        mb.box(HX + x0, HX + x1, HY + y0, HY + y1, zt - 0.02, zt, "heli_white", skip=("bottom",))
    ring(mb, HX, HY, RG - 0.2, zt, RG - 0.45, zt, "heli_white", n)        # touchdown circle
    # Safety net: fixed winding (r0 > r1 faces +Z up, r0 < r1 faces -Z down -> zero back-face holes)
    ring(mb, HX, HY, RDK + HNET, HZT - 0.12, RDK, HZT - 0.12, "heli_net", n)              # net top (+Z)
    ring(mb, HX, HY, RDK, HZT - 0.18, RDK + HNET, HZT - 0.18, "heli_net", n)              # net bottom (-Z)
    ring(mb, HX, HY, RDK + HNET, HZT - 0.18, RDK + HNET, HZT - 0.12, "heli_net", n)       # net outer rim
    # Perimeter safety railing + posts round the net outer edge
    rn = RDK + HNET - 0.04
    for i in range(n):
        a, b = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p0, p1 = (HX + rn * math.cos(a), HY + rn * math.sin(a)), (HX + rn * math.cos(b), HY + rn * math.sin(b))
        prism(mb, (p0[0], p0[1], HZT + 0.78), (p1[0], p1[1], HZT + 0.78), 0.045, "railing")
        if stage == 0:
            prism(mb, (p0[0], p0[1], HZT + 0.36), (p1[0], p1[1], HZT + 0.36), 0.035, "railing")
            if i % 2 == 0:
                mb.box(p0[0] - 0.025, p0[0] + 0.025, p0[1] - 0.025, p0[1] + 0.025,
                       HZT - 0.12, HZT + 0.80, "railing", skip=("bottom",))
    for i in range(8):                                                     # struts collar -> underside
        a = 2 * math.pi * (i + 0.5) / 8
        prism(mb, (HX + (HCORE + 0.08) * math.cos(a), HY + (HCORE + 0.08) * math.sin(a), (zc0 + zc1) / 2),
              (HX + 0.8 * RDK * math.cos(a), HY + 0.8 * RDK * math.sin(a), HZ0 + 0.8 * (HZ1 - HZ0) - 0.15),
              0.32, "crown_white")
    # Access stair + landing on the south roof (between helipad deck and crown plinth, y=15.3..18.8)
    _heli_access(mb, stage)
    if stage == 0:
        for i in range(16):
            a = 2 * math.pi * (i + 0.5) / 16
            x, y = HX + (RDK - 0.4) * math.cos(a), HY + (RDK - 0.4) * math.sin(a)
            mb.box(x - 0.08, x + 0.08, y - 0.08, y + 0.08, HZT, HZT + 0.1, "heli_light", skip=("bottom",))
        for i in range(12):
            a = 2 * math.pi * (i + 0.5) / 12
            x, y = HX + (RG - 0.32) * math.cos(a), HY + (RG - 0.32) * math.sin(a)
            mb.box(x - 0.06, x + 0.06, y - 0.06, y + 0.06, HZT, HZT + 0.08, "heli_light_y", skip=("bottom",))
        for i in range(8):
            a = 2 * math.pi * (i + 0.5) / 8
            d = 4.6
            x, y = HX + d * math.cos(a), HY + d * math.sin(a)
            z = HZ0 + (HZ1 - HZ0) * (d - HCORE) / (RDK - HCORE)
            mb.box(x - 0.25, x + 0.25, y - 0.25, y + 0.25, z - 0.14, z - 0.02, "under_light", skip=("top",))
        # Windsock mast on NE net corner
        mx, my, zn = HX + (RDK + HNET - 0.25) * math.cos(-0.65), HY + (RDK + HNET - 0.25) * math.sin(-0.65), HZT - 0.12
        mb.box(mx - 0.05, mx + 0.05, my - 0.05, my + 0.05, zn, zn + 2.8, "crown_white", skip=("bottom", "top"))
        mb.box(mx - 0.08, mx + 0.08, my - 0.08, my + 0.08, zn + 2.8, zn + 3.0, "obst_light", skip=("bottom",))
        mb.box(mx + 0.05, mx + 0.85, my - 0.15, my + 0.15, zn + 2.3, zn + 2.6, "windsock", skip=("left",))


def _heli_access(mb, stage):
    """Straight steel access stair rising from main roof (y=18.8) to the helipad south bridge (y=15.3)."""
    x0, x1 = HX - 0.65, HX + 0.65
    ya, yb = 18.7, HY + RDK - 0.2
    y_br0 = HY + RDK + HNET + 0.1
    # Top bridge over the net (kept clear above HZT - 0.12 so no overlap)
    mb.box(x0, x1, yb, y_br0, HZT, HZT + 0.08, "grating")
    for x in (x0 + 0.06, x1 - 0.06):
        mb.box(x - 0.06, x + 0.06, y_br0 - 0.06, y_br0 + 0.06, H, HZT, "crown_white", skip=("bottom", "top"))
        prism(mb, (x, ya, H - 0.12), (x, y_br0, HZT - 0.02), 0.08, "crown_white")
        prism(mb, (x, ya, H + 0.9), (x, y_br0, HZT + 0.9), 0.04, "railing")
        prism(mb, (x, y_br0, HZT + 0.9), (x, yb, HZT + 0.9), 0.04, "railing")
        if stage == 0:
            for py, pz in ((ya, H), ((ya + y_br0) / 2, (H + HZT) / 2), (y_br0, HZT), (yb + 0.1, HZT)):
                mb.box(x - 0.03, x + 0.03, py - 0.03, py + 0.03, pz, pz + 0.90, "railing", skip=("bottom",))
    if stage == 0:
        n = 18
        for i in range(n):
            yy0 = ya + (y_br0 - ya) * i / n
            yy1 = ya + (y_br0 - ya) * (i + 1) / n
            zt = H + (HZT - H) * (i + 1) / n
            mb.box(x0 + 0.11, x1 - 0.11, yy1 + 0.02, yy0 - 0.02, zt - 0.05, zt, "grating")


def roof(mb, stage):
    for x0, x1, y0, y1 in ROOF_RECTS:
        mb.rect([(x0, y0, H), (x1, y0, H), (x1, y1, H), (x0, y1, H)], "roof")
    parapet_ring(mb)
    crown(mb, stage)
    helipad(mb, stage)
    if stage == 0:
        for xc, yc in ((-X + 0.2, 0.2), (15.0 - X - 0.2, 0.2), (X - 0.2, 14.6), (10.6 - 0.2, D - 0.2),
                       (-X + 0.2, D - 0.2)):
            mb.box(xc - 0.12, xc + 0.12, yc - 0.12, yc + 0.12, PH, PH + 0.25, "obst_light", skip=("bottom",))


# ==============================================================================
# ENTRANCE PORTICO on the main body north wall (y = ENT_Y): built at y = 0, then shifted
# ==============================================================================
EY = -3.95
EZ0, EZB, EZC, EZT = 3.70, 4.72, 5.48, 5.98     # EZT=5.98 kisses 2F sill (5.99) with win_blocked=0
PORTICO_X0, PORTICO_X1 = 10.6, 19.2             # portico on the arm wall, pink pier at outer corner
LP = 1.2
PIER_X0 = PORTICO_X1 - 2.15                     # 17.05 -> 5.25 m lintel span (matches paint_ent_lintel)
ST_N, ST_R, ST_T = 7, 0.15, 0.34                # yl=-1.57 -> ENT_Y+yl=12.83 > ㄷ자 ramp yo0=12.70


def _revolving_door(mb, cx, cy, z0, z1, r=1.05):
    """Cylindrical brushed-stainless revolving canopy & glass quadrants in local portico coords."""
    zc0, zc1 = z1 - 0.32, z1
    n = 16
    pts = [(cx + r * math.cos(math.pi + math.pi * k / n), cy + r * math.sin(math.pi + math.pi * k / n))
           for k in range(n + 1)]
    for k in range(n):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        mb.rect([(x0, y0, zc0), (x1, y1, zc0), (x1, y1, zc1), (x0, y0, zc1)], "stainless")
    for k in range(0, n, 2):
        (x0, y0), (xm, ym), (x1, y1) = pts[k], pts[k + 1], pts[k + 2]
        mb.rect([(cx, cy, zc1), (x0, y0, zc1), (xm, ym, zc1), (x1, y1, zc1)], "stainless")
        mb.rect([(cx, cy, zc0), (x1, y1, zc0), (xm, ym, zc0), (x0, y0, zc0)], "stainless")
    mb.rect([(cx + r, cy, zc0), (cx - r, cy, zc0), (cx - r, cy, zc1), (cx + r, cy, zc1)], "stainless")
    # Two curved fixed glass wings flanking the open front entryway
    rin = r - 0.06
    for th0, th1, steps in ((math.pi, math.pi * 1.34, 4), (math.pi * 1.66, math.pi * 2.0, 4)):
        ths = [th0 + (th1 - th0) * k / steps for k in range(steps + 1)]
        for zb, zt, mat in ((z0, z0 + 0.14, "stainless"), (z0 + 0.14, zc0 - 0.06, "rev_glass"),
                            (zc0 - 0.06, zc0, "stainless")):
            for k in range(steps):
                a, b = ths[k], ths[k + 1]
                ox0, oy0 = cx + r * math.cos(a), cy + r * math.sin(a)
                ox1, oy1 = cx + r * math.cos(b), cy + r * math.sin(b)
                ix0, iy0 = cx + rin * math.cos(a), cy + rin * math.sin(a)
                ix1, iy1 = cx + rin * math.cos(b), cy + rin * math.sin(b)
                mb.rect([(ox0, oy0, zb), (ox1, oy1, zb), (ox1, oy1, zt), (ox0, oy0, zt)], mat)
                mb.rect([(ix1, iy1, zb), (ix0, iy0, zb), (ix0, iy0, zt), (ix1, iy1, zt)], mat)
        for edge_th, flip in ((th0, False), (th1, True)):
            ox, oy = cx + r * math.cos(edge_th), cy + r * math.sin(edge_th)
            ix, iy = cx + rin * math.cos(edge_th), cy + rin * math.sin(edge_th)
            q = [(ox, oy, z0), (ix, iy, z0), (ix, iy, zc0), (ox, oy, zc0)]
            mb.rect(q if flip else q[::-1], "stainless")
    # Central hub + angled revolving rotor leaves strictly forward of the vestibule wall (y <= -0.10)
    hc_y = cy - 0.12
    mb.box(cx - 0.08, cx + 0.08, hc_y - 0.08, hc_y + 0.08, z0, zc0, "stainless", skip=("bottom", "top"))
    for ang_deg in (236, 304):
        rad = math.radians(ang_deg)
        dx, dy = math.cos(rad), math.sin(rad)
        nx, ny = -dy * 0.022, dx * 0.022
        px0, py0 = cx + 0.08 * dx, hc_y + 0.08 * dy
        px1, py1 = cx + 0.84 * dx, hc_y + 0.84 * dy
        for z_a, z_b, mat in ((z0 + 0.08, zc0 - 0.08, "rev_glass"),):
            mb.rect([(px0 + nx, py0 + ny, z_a), (px1 + nx, py1 + ny, z_a),
                     (px1 + nx, py1 + ny, z_b), (px0 + nx, py0 + ny, z_b)], mat)
            mb.rect([(px1 - nx, py1 - ny, z_a), (px0 - nx, py0 - ny, z_a),
                     (px0 - nx, py0 - ny, z_b), (px1 - nx, py1 - ny, z_b)], mat)
            mb.rect([(px1 + nx, py1 + ny, z_a), (px1 - nx, py1 - ny, z_a),
                     (px1 - nx, py1 - ny, z_b), (px1 + nx, py1 + ny, z_b)], "stainless")


def entrance(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    x_l = PORTICO_X0 + LP
    mb.box(PORTICO_X0 - 0.1, x_l, EY - 0.15, EY + 1.1, 0, EZC, "stone", skip=("bottom", "top"))
    # Side-portal soffits & outer clerestory bands behind the left column and right pier
    mb.box(PORTICO_X0, x_l, EY + 1.1, 0.0, EZ0, EZC,
           dict(left="pale", right="pale", bottom="soffit", default="pale"), skip=("back", "top", "front"))
    mb.box(PIER_X0, PORTICO_X1, EY + 1.8, 0.0, EZ0, EZC,
           dict(right="pale", left="pale", bottom="soffit", default="pale"), skip=("back", "top", "front"))
    # Travertine EXLLU TOWER lintel (3.70..4.72) + recessed transom clerestory (4.72..5.48) + continuous top coping (5.48..5.98)
    mb.box(x_l, PIER_X0, EY + 0.02, 0.0, EZ0, EZB,
           dict(bottom="soffit", top="stone_trim", default="pale"),
           skip=("back", "left", "right", "front"))
    mb.box(x_l, PIER_X0, EY + 0.12, 0.0, EZB, EZC,
           dict(bottom="soffit", default="stone_trim"), skip=("back", "top", "left", "right"))
    mb.box(PORTICO_X0 - 0.15, PORTICO_X1 + 0.25, EY - 0.20, 0.0, EZC, EZT,
           dict(top="roof", default="stone"), skip=("back",))
    if stage == 2:
        mb.rect(K.face_pts("y", EY + 0.02, -1, x_l, PIER_X0, EZ0, EZB), "pale")
        mb.box(PIER_X0, PORTICO_X1 + 0.2, EY - 0.15, EY + 0.65, 0, EZC, "pier_pink", skip=("bottom", "top", "back"))
        mb.box(PIER_X0, PORTICO_X1 + 0.2, EY + 0.65, EY + 1.8, 0, EZC, "stone", skip=("bottom", "top", "front"))
    if stage < 2:
        # Carved travertine lintel front face (11.80..17.05 x 3.70..4.72 = 5.25 x 1.02 m)
        mb.quad(K.face_pts("y", EY + 0.02, -1, x_l, PIER_X0, EZ0, EZB), A.uv_full("ent_lintel"), "ent_lintel")
        # Front transom clerestory + 4 vertical + 1 horizontal center mullion bars
        K.paint(mb, "y", EY + 0.12, -1, x_l + 0.15, PIER_X0 - 0.15, EZB + 0.07, EZC - 0.07, "clerestory", layer=2)
        for mx in (x_l + 1.05, x_l + 2.10, x_l + 3.15, x_l + 4.20):
            K.paint(mb, "y", EY + 0.12, -1, mx - 0.025, mx + 0.025, EZB + 0.04, EZC - 0.04, "frame", layer=3)
        zm = (EZB + EZC) / 2
        K.paint(mb, "y", EY + 0.12, -1, x_l, PIER_X0, zm - 0.025, zm + 0.025, "frame", layer=4)
        # Side portal clerestories
        for c, s, a0, a1 in ((PORTICO_X0, -1, EY + 1.1, 0.0), (PORTICO_X1, 1, EY + 1.8, 0.0)):
            K.paint(mb, "x", c, s, a0, a1, EZ0, EZB, "stone", layer=2)
            K.paint(mb, "x", c, s, a0 + 0.2, a1 - 0.2, EZB + 0.07, EZC - 0.07, "clerestory", layer=2)
            K.paint(mb, "x", c, s, a0, a1, EZB, EZB + 0.07, "frame", layer=3)
        # Right corner pier: smooth pink inner slab (1.40 m, DONG gold numerals) + split-face outer course (0.65 m) + dark outer frame
        px_mid = PIER_X0 + 1.40
        px_out = px_mid + 0.65
        mb.box(PIER_X0, px_mid, EY - 0.15, EY + 0.65, 0, EZC, dict(left="pier_pink", default="pier_pink"),
               skip=("bottom", "top", "back", "front", "right"))
        for z0, z1, mat, full in ((0.0, 2.05, "pier_pink", False),
                                  (2.05, 3.15, "pier_num", True),
                                  (3.15, EZC, "pier_pink", False)):
            pts = K.face_pts("y", EY - 0.15, -1, PIER_X0, px_mid, z0, z1)
            if full:
                mb.quad(pts, A.uv_full(mat), mat)
            else:
                mb.rect(pts, mat)
        mb.box(px_mid, px_out, EY - 0.15, EY + 0.65, 0, EZC,
               dict(front="pier_course", right="pier_pink", default="pier_pink"),
               skip=("bottom", "top", "left", "back"))
        mb.box(px_out, PORTICO_X1 + 0.20, EY - 0.15, EY - 0.04, 0, EZC, "stone", skip=("bottom", "top", "left"))
        mb.box(px_out, PORTICO_X1 + 0.20, EY - 0.04, EY + 0.65, 0, EZC, "pier_pink", skip=("bottom", "top", "left", "front", "back"))
        # Tiny dark granite/steel square sconce centered above gold DONG numerals on pink pier
        mb.box(PIER_X0 + 0.62, PIER_X0 + 0.78, EY - 0.22, EY - 0.15, 3.22, 3.38,
               dict(bottom="ent_light", default="stone"), skip=("back",))
        # Rear dark granite pier wrap + gold DONG numerals on +X face (1.15 x 1.10 m)
        mb.box(PIER_X0, PORTICO_X1 + 0.20, EY + 0.65, EY + 1.80, 0, EZC,
               dict(left="stone_trim", back="stone", default="stone"),
               skip=("bottom", "top", "front", "right"))
        for z0, z1, mat, full in ((0.0, 2.05, "stone", False),
                                  (2.05, 3.15, "pier_side_num", True),
                                  (3.15, EZC, "stone", False)):
            pts = K.face_pts("x", PORTICO_X1 + 0.20, 1, EY + 0.65, EY + 1.80, z0, z1)
            if full:
                mb.quad(pts, A.uv_full(mat), mat)
            else:
                mb.rect(pts, mat)
        yl = EY + ST_N * ST_T
        zl = ST_N * ST_R
        # Left stair cheek ends at yl so the behind-pillar bridge opens onto the main landing (ㄷ자 ramp entry)
        mb.box(x_l - 0.3, x_l, EY + 1.1, yl, 0, zl, "stone_trim", skip=("bottom", "front", "back"))
        mb.box(PORTICO_X0, PORTICO_X0 + LP, yl, 0.0, 0, zl, dict(top="canopy", default="stone_trim"),
               skip=("bottom", "back", "left", "right"))
        # Right cheek curb inside portico right opening: low step along stairs + landing height in back
        mb.box(PIER_X0, PIER_X0 + 0.25, EY + 1.8, yl, 0, 0.68, "stone_trim", skip=("bottom", "front", "back"))
        mb.box(PIER_X0, PIER_X0 + 0.25, yl, 0.0, 0, zl, "stone_trim", skip=("bottom", "front", "back"))
        # Built-in granite planter & green shrubs inside the portico right portal (view_nw_base + side photo)
        mb.box(PIER_X0 + 0.25, PORTICO_X1 + 0.08, EY + 1.8, 0.0, 0, 0.42,
               dict(top="soil", default="stone_trim"), skip=("bottom", "front", "back", "left"))
        for ya_s, yb_s, z_s in ((EY + 1.92, EY + 2.54, 0.78), (EY + 2.58, EY + 3.24, 0.92), (EY + 3.28, -0.08, 0.84)):
            mb.box(PIER_X0 + 0.34, PORTICO_X1 - 0.02, ya_s, yb_s, 0.42, z_s, "foliage", skip=("bottom",))
        for i in range(ST_N):
            y0 = EY + i * ST_T
            mb.box(PORTICO_X0 + LP, PIER_X0, y0, y0 + ST_T, 0, ST_R * (i + 1), "canopy",
                   skip=("bottom", "back", "left", "right"))
        mb.box(PORTICO_X0 + LP, PIER_X0, yl, 0, 0, zl, "canopy", skip=("bottom", "back", "left", "right"))
        mb.box(PORTICO_X0 + LP, PIER_X0, -0.05, 0.0, zl, EZ0, {"front": "vestibule", "default": "stone_trim"},
               skip=("bottom", "top", "back", "left", "right"))
        # Cylindrical brushed-stainless revolving door + right vestibule swing doors
        _revolving_door(mb, 13.70, -0.10, zl, zl + 2.55, r=1.05)
        # Multi-bar stair and landing handrails + vertical posts on both sides (posts 0.06 > rails 0.04 -> zero coplanar)
        ya = EY + 0.2
        rail_z = lambda y: ST_R + (y - ya) / (yl + 0.06 - ya) * (zl - ST_R)
        xl, xr = PORTICO_X0 + LP + 0.10, PIER_X0 - 0.08
        for dz in (0.90, 0.72, 0.54, 0.36, 0.18):
            rw = 0.028 if dz < 0.9 else 0.04
            prism(mb, (xl, ya, dz + rail_z(ya)), (xl, yl + 0.06, dz + zl), rw, "railing")
            prism(mb, (xr, ya, dz + rail_z(ya)), (xr, yl + 0.06, dz + zl), rw, "railing")
            prism(mb, (xr, yl + 0.06, dz + zl), (xr, -0.05, dz + zl), rw, "railing")
        for x_side in (xl, xr):
            for k in range(4):
                yy = ya + k * (yl + 0.06 - ya) / 3
                zb = min(zl, ST_R * min(ST_N, 1 + int((yy - EY) / ST_T)))
                mb.box(x_side - 0.03, x_side + 0.03, yy - 0.03, yy + 0.03, zb, 0.90 + rail_z(yy), "railing", skip=("bottom",))
        for yy in ((yl + 0.06) / 2, -0.05):
            mb.box(xr - 0.03, xr + 0.03, yy - 0.03, yy + 0.03, zl, zl + 0.90, "railing", skip=("bottom",))
    mb.verts = [(x, y + ENT_Y, z) for x, y, z in mb.verts]
    if stage < 2:
        # Left ㄷ자 folded accessible ramp (106/108 photo: ground entry -> lower run left -> U-turn landing -> inner run right -> terrace behind pillar)
        y_lf = ENT_Y + yl
        rx_t0, rx_t1, rx_r1, rx_o1 = -2.0, -0.6, 6.8, 5.8
        yo0, yo1, yc0, yc1, yi0, yi1 = 12.70, 13.95, 13.95, 14.10, 14.10, 15.40
        z_r0, z_mid, zl = 0.04, 0.54, ST_N * ST_R
        zo_at = lambda x: z_mid + max(0.0, min(1.0, (x - rx_t1) / (rx_o1 - rx_t1))) * (z_r0 - z_mid)
        zi_at = lambda x: z_mid + max(0.0, min(1.0, (x - rx_t1) / (rx_r1 - rx_t1))) * (zl - z_mid)
        # Mid-landing 180-deg turn on left
        mb.box(rx_t0, rx_t1, yo0, yi1, 0.0, z_mid, dict(top="canopy", default="stone_trim"), skip=("bottom", "back", "right"))
        # Outer lower ramp wedge (slopes down rightwards to ground plaza threshold at x=5.8)
        mb.rect([(rx_t1, yo0, z_mid), (rx_o1, yo0, z_r0), (rx_o1, yo1, z_r0), (rx_t1, yo1, z_mid)], "canopy")
        mb.rect([(rx_t1, yo0, 0.0), (rx_o1, yo0, 0.0), (rx_o1, yo0, z_r0), (rx_t1, yo0, z_mid)], "stone_trim")
        mb.rect([(rx_o1, yo0, 0.0), (rx_o1, yo1, 0.0), (rx_o1, yo1, z_r0), (rx_o1, yo0, z_r0)], "stone_trim")
        # Center divider retaining wall (follows inner ramp height -> flush zl at x=6.8)
        mb.rect([(rx_t1, yc0, z_mid), (rx_r1, yc0, zl), (rx_r1, yc1, zl), (rx_t1, yc1, z_mid)], "stone_trim")
        mb.rect([(rx_t1, yc0, 0.0), (rx_r1, yc0, 0.0), (rx_r1, yc0, zl), (rx_t1, yc0, z_mid)], "stone_trim")
        # Inner upper ramp sloped surface (0.54 at -0.6 up to 1.05 at 6.8 along y=15.4 wall)
        mb.rect([(rx_t1, yi0, z_mid), (rx_r1, yi0, zl), (rx_r1, yi1, zl), (rx_t1, yi1, z_mid)], "canopy")
        # Upper terrace in front of 1F landing window (x=6.8..10.6 -> connects behind left pillar onto portico landing)
        mb.box(rx_r1, PORTICO_X0, y_lf, yi1, 0.0, zl, dict(top="canopy", default="stone_trim"), skip=("bottom", "back", "right"))
        # Small foreground shrub planter beside plaza ramp entry (106 photo)
        mb.box(rx_r1 + 0.3, PORTICO_X0 - 0.15, y_lf - 0.65, y_lf, 0.0, 0.42,
               dict(top="soil", default="stone_trim"), skip=("bottom", "back"))
        mb.box(rx_r1 + 0.42, PORTICO_X0 - 0.27, y_lf - 0.55, y_lf - 0.08, 0.42, 0.80, "foliage", skip=("bottom",))
        # Continuous 5-bar guardrails + posts for the entire ㄷ자 path
        yo_r, xl_r, yc_r, yt_r, x_lport = yo0 + 0.06, rx_t0 + 0.06, (yc0 + yc1) / 2, y_lf + 0.06, PORTICO_X0 + LP + 0.10
        for dz in (0.90, 0.72, 0.54, 0.36, 0.18):
            rw = 0.028 if dz < 0.9 else 0.04
            prism(mb, (rx_o1 - 0.1, yo_r, dz + zo_at(rx_o1 - 0.1)), (rx_t1, yo_r, dz + z_mid), rw, "railing")
            prism(mb, (rx_t1, yo_r, dz + z_mid), (xl_r, yo_r, dz + z_mid), rw, "railing")
            prism(mb, (xl_r, yo_r, dz + z_mid), (xl_r, yi1 - 0.06, dz + z_mid), rw, "railing")
            prism(mb, (rx_t1 + 0.1, yc_r, dz + zi_at(rx_t1 + 0.1)), (rx_r1, yc_r, dz + zl), rw, "railing")
            prism(mb, (rx_r1, yc_r, dz + zl), (rx_r1, yt_r, dz + zl), rw, "railing")
            prism(mb, (rx_r1, yt_r, dz + zl), (x_lport, yt_r, dz + zl), rw, "railing")
        def _post(px, py, zb, z_base_rail=None):
            zr = zb if z_base_rail is None else z_base_rail
            mb.box(px - 0.03, px + 0.03, py - 0.03, py + 0.03, zb, zr + 0.90, "railing", skip=("bottom",))
        for k in range(6):
            xx = (rx_o1 - 0.1) + (rx_t1 - (rx_o1 - 0.1)) * k / 5
            _post(xx, yo_r, zo_at(xx))
        _post(xl_r, yo_r, z_mid)
        _post(xl_r, (yo_r + yi1 - 0.06) / 2, z_mid)
        _post(xl_r, yi1 - 0.06, z_mid)
        for k in range(6):
            xx = (rx_t1 + 0.1) + (rx_r1 - (rx_t1 + 0.1)) * k / 5
            _post(xx, yc_r, zi_at(xx))
        _post(rx_r1, yt_r, zl)
        _post((rx_r1 + PORTICO_X0) / 2, yt_r, zl)
        _post(PORTICO_X0, yt_r, zl)
    if stage == 0:
        # Warm pier sconces
        mb.box(PORTICO_X0 + LP, PORTICO_X0 + LP + 0.05, ENT_Y + EY + 0.4, ENT_Y + EY + 0.7, 2.5, 2.85,
               "ent_light", skip=("left",))
        mb.box(PIER_X0 - 0.05, PIER_X0, ENT_Y + EY + 0.4, ENT_Y + EY + 0.7, 2.5, 2.85,
               "ent_light", skip=("right",))
    return mb


# ==============================================================================
# MAIN BUILDING ASSEMBLY
# ==============================================================================
CORE_WALLS = {1, 2, 3, 5, 9, 10, 11, 12, 16, 18}


def _wall_span(mb, x0, y0, x1, y1, z0, z1, mat):
    mb.rect([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], mat)


def _zoned_wall(mb, idx, ax, ay, bx, by, zp, stage):
    if stage == 2:
        _wall_span(mb, ax, ay, bx, by, 0.0, zp, "stone")
        _wall_span(mb, ax, ay, bx, by, zp, H, "pale")
        return
    if idx in CORE_WALLS:
        _wall_span(mb, ax, ay, bx, by, 0.0, zp, "stone")
        _wall_span(mb, ax, ay, bx, by, zp, H, "mid_grey")
        return
    belts = ((0.0, zp, "stone"), (zp, zf(10), "cool_pale"), (zf(10), zf(14), "mid_grey"),
             (zf(14), zf(36), "pale"), (zf(36), zf(40), "mid_grey"), (zf(40), H, "pale"))
    if idx != 14:
        for z0, z1, mat in belts:
            _wall_span(mb, ax, ay, bx, by, z0, z1, mat)
        return
    # Wall 14 (south main facade, ax=10.6 -> bx=-19.2 at y=44.6): tripartite wings + flush central crown shaft
    for x0, x1 in ((ax, CROWN_X1), (CROWN_X0, bx)):
        for z0, z1, mat in belts:
            _wall_span(mb, x0, ay, x1, by, z0, z1, mat)
    ew = 0.50
    _wall_span(mb, CROWN_X1, ay, CROWN_X0, by, 0.0, zp, "stone")
    zc0 = zf(CROWN_F0)
    for x0, x1, mat in ((CROWN_X1, CROWN_X1 - ew, "dark_paint"),
                        (CROWN_X1 - ew, CROWN_X0 + ew, "mid_grey"),
                        (CROWN_X0 + ew, CROWN_X0, "dark_paint")):
        _wall_span(mb, x0, ay, x1, by, zp, zc0, mat)
    for x0, x1, mat in ((CROWN_X1, CROWN_X1 - ew, "crown_white"),
                        (CROWN_X1 - ew, CROWN_X0 + ew, "crown_glass"),
                        (CROWN_X0 + ew, CROWN_X0, "crown_white")):
        _wall_span(mb, x0, ay, x1, by, zc0, H, mat)


def build(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    n = len(OUTLINE)
    for i in range(n):                         # outer walls straight from the outline
        (ax, ay), (bx, by) = OUTLINE[i], OUTLINE[(i + 1) % n]
        zp = zf(PORTICO_PALE_F if i in (5, 6, 7, 8) else PALE_F)
        _zoned_wall(mb, i, ax, ay, bx, by, zp, stage)
    roof(mb, stage)
    mb.merge(entrance(stage))
    if stage < 2:
        ledges(mb)
    if stage == 0:
        facade_floor(mb, stage, 0, skip=(PORTICO_X0 - 0.5, PORTICO_X1 + 0.5))
        for f in range(1, NF):
            facade_floor(mb, stage, f)
    return mb


main = build(0)
lod1 = build(1)
lod2 = build(2)

K.export_asset(ASSET, 1, dict(main=main, lod1=lod1, lod2=lod2, windows=WS),
               A, K.out_dir_from_argv("output"), lot=(5, 6))
