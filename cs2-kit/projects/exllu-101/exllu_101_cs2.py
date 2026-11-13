"""Tower 101: 36-floor Type B tower, two staggered slabs joined by a core, flat segmented roof, modern portico.

Evidence: complex aerial (exllu-105/photos/dong_crops/grid.png: 101/104/109/112 show two offset slabs,
a central link with open light slots, stepped corners and NO helipad), entrance photos of 101/109/111/112.
Custom generator for Kumgang Exllu Tower 101 (27~28 py small/mid units, 36 floors, 108.0 m roof slab, 113.4 m total w/ masts).
Copied from exllu-104 (same B type, identical OSM outline); facade evidence is tower 104 photos, not 101.
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

DONG = "101"
ASSET = f"HighriseTower{DONG}"

W, D, FH, NF = 29.7, 22.8, 2.94, 36          # 36 floors, 29.7 x 22.8 m footprint (OSM way 934368139) + 4 m portico
GH = 5.10                                     # double-height lobby storey (allows portico cap below 2F sill)
H = GH + FH * (NF - 1)                        # 108.00 m roof slab; core penthouse coping 112.54 m, beacons 113.1 m, masts 113.4 m
REF_F = None                                  # 36-floor tower has standard residential floors throughout


def zf(f):
    """Floor level of storey f (0 = lobby)."""
    return 0.0 if f == 0 else GH + (f - 1) * FH


X = W / 2                                     # 14.85 m
LEDGE_P, LEDGE_T = 0.09, 0.12                 # refined per-floor horizontal ledge projection / thickness
SILL, HEAD = 0.82, 2.62                       # window sill and head heights (1.80 m glazing, photo 155809)


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
    ctx.rgb[...] = np.array([96, 146, 168], np.float32) + ((h - 0.5) * 16)[..., None]
    ctx.rgb += (fv * 42 - 4)[..., None]
    m = (fu * 0.7 + fv) % 1.0
    ctx.rgb += (((m > 0.30) & (m < 0.37)) * 20.0)[..., None]
    ctx.rgb += (((m > 0.62) & (m < 0.64)) * 12.0)[..., None]
    edge = np.minimum(np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv))
    ctx.rgb *= (0.80 + 0.20 * np.clip(edge / 0.035, 0, 1))[..., None]
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


def hopper_vent(ctx):
    """Recessed upper awning/hopper vent sash + deep shadowed glazing (photos 155809/155129)."""
    nu = np.minimum(ctx.u, 1.0 - ctx.u) / 0.075
    nv = np.minimum(ctx.v, 1.0 - ctx.v) / 0.045
    s = np.minimum(nu, nv)
    sash_outer = s < 1.0
    sash_inner = (s >= 1.0) & (s < 2.0)
    glass = s >= 2.0
    ctx.rgb[glass] = np.array([48, 84, 106], np.float32) + ((ctx.v[glass] - 0.5) * 14.0)[..., None]
    # Subtle top-edge hinge / head-overhang shadow inside recessed cavity
    top_sh = np.clip(1.0 - np.maximum(0.0, ctx.v - 0.72) / 0.28 * 0.25, 0.72, 1.0)
    ctx.rgb[glass] *= top_sh[glass, None]
    ctx.rgb[sash_inner] = np.array([204, 210, 214], np.float32)
    ctx.rgb[sash_outer] = np.array([34, 42, 52], np.float32)
    ctx.height[sash_outer] = 0.0
    ctx.height[sash_inner] = 0.8
    ctx.height[glass] = 0.3
    ctx.gloss[sash_outer] = 0.12
    ctx.gloss[sash_inner] = 0.45
    ctx.gloss[glass] = 0.78


def soil(ctx):
    ctx.grain(amp=12.0, scale_px=2, height=0.8, seed=14)
    ctx.rgb += ctx.noise(16, 10.0, 3, seed=15)[..., None]


def brushed_stainless(ctx):
    """Fine horizontal brushed stainless steel grain for drum crown, mullions & roof ducts."""
    k = ctx.w / 128.0
    ctx.rgb += ctx.noise(max(4, int(16 * k)), 6.0, 2, seed=31)[..., None] * 0.4
    ctx.rgb += (3.5 * ctx.noise(max(16, int(48 * k)), 1.0, 2, seed=32))[..., None] * 0.6
    d = np.minimum(ctx.v, 1.0 - ctx.v)
    ctx.rgb[d < 0.05] *= 0.80
    ctx.gloss[...] = np.clip(0.80 + 0.08 * ctx.noise(max(4, int(12 * k)), 1.0, 2, seed=33), 0.65, 0.92)


def fan_grille(ctx):
    """Rooftop HVAC exhaust fan cowling grille + radial blades."""
    dx, dy = ctx.u - 0.5, ctx.v - 0.5
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)
    blade = (r < 0.40) & (np.sin(5.0 * ang + r * 4.5) > 0.25)
    ring = (r < 0.44) & (np.abs((r * 11.0) % 1.0 - 0.5) < 0.09)
    rim = (r >= 0.42) & (r <= 0.49)
    cavity = r < 0.42
    ctx.rgb[cavity] = np.array([26, 30, 36], np.float32)
    ctx.rgb[blade] = np.array([112, 118, 126], np.float32)
    ctx.rgb[ring] = np.array([186, 190, 194], np.float32)
    ctx.rgb[rim] = np.array([196, 200, 204], np.float32)
    ctx.height[cavity] = 0.0
    ctx.height[blade] = 0.45
    ctx.height[ring | rim] = 0.9
    ctx.gloss[cavity] = 0.25
    ctx.gloss[blade | ring | rim] = 0.65


def rev_glass(ctx):
    """Curved revolving-door architectural glass with vertical specular reflection & soft lobby glow."""
    mx, mz = ctx.meters()
    ctx.rgb += (ctx.v * 28.0 - 6.0)[..., None]
    streak = ((ctx.u * 0.65 + ctx.v) % 1.0)
    ctx.rgb += (((streak > 0.25) & (streak < 0.36)) * 18.0)[..., None]
    edge = (mx < 0.015) | (mx > ctx.tile[0] - 0.015) | (mz < 0.015) | (mz > ctx.tile[1] - 0.015)
    ctx.rgb[edge] *= 0.65
    ctx.emis[...] = np.where(edge, 0.0, 0.14)
    ctx.gloss[...] = 0.90


def foliage(ctx):
    ctx.grain(amp=16.0, scale_px=3, height=1.0, seed=21)
    ctx.rgb += ctx.noise(12, 14.0, 3, seed=22)[..., None]
    ctx.rgb[:, :, 1] += 8.0 * ctx.noise(8, 1.0, 2, seed=23)


def flat_emis(v):
    return lambda c: c.emis.__setitem__(Ellipsis, v)


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
    "2": ((0.18, 0.74, 0.32, 0.90), (0.32, 0.90, 0.70, 0.90), (0.70, 0.90, 0.84, 0.76), (0.84, 0.76, 0.84, 0.62),
          (0.84, 0.62, 0.16, 0.10), (0.16, 0.10, 0.86, 0.10)),
    "3": ((0.18, 0.76, 0.32, 0.90), (0.32, 0.90, 0.70, 0.90), (0.70, 0.90, 0.84, 0.76), (0.84, 0.76, 0.84, 0.62),
          (0.84, 0.62, 0.70, 0.52), (0.70, 0.52, 0.42, 0.52), (0.70, 0.52, 0.86, 0.38), (0.86, 0.38, 0.86, 0.24),
          (0.86, 0.24, 0.70, 0.10), (0.70, 0.10, 0.30, 0.10), (0.30, 0.10, 0.16, 0.22)),
    "4": ((0.70, 0.10, 0.70, 0.90), (0.70, 0.90, 0.14, 0.34), (0.14, 0.34, 0.88, 0.34)),
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
    "9": ((0.24, 0.10, 0.66, 0.10), (0.66, 0.10, 0.84, 0.30), (0.84, 0.30, 0.84, 0.74), (0.84, 0.74, 0.66, 0.90),
          (0.66, 0.90, 0.28, 0.90), (0.28, 0.90, 0.14, 0.74), (0.14, 0.74, 0.14, 0.58), (0.14, 0.58, 0.30, 0.46),
          (0.30, 0.46, 0.84, 0.46)),
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
    items = [("E", 1.0), ("X", 1.0), ("L", 1.44), ("L", 1.76), ("U", 1.0),
             (" ", 0.72), ("T", 0.90), ("O", 0.90), ("W", 0.98), ("E", 0.90), ("R", 0.90)]
    adv = ch_w * 1.18
    x_pos = cx - adv * 5.05
    for idx, (ch, hs) in enumerate(items):
        gw = ch_w * (0.82 if ch == "L" else (1.06 if ch == "W" else (0.92 if idx > 5 else 0.96)))
        gh = ch_h * hs
        if ch == "L":
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


def paint_ent_lintel(ctx, w_m=5.85, h_m=0.84):
    granite(ctx, 5, 1, 0.14, 2.8, 0.10)
    px, py = ctx.u * w_m, ctx.v * h_m
    segs = _exllu_segs(w_m * 0.50, h_m * 0.25, 0.18, 0.27)
    d = _sdf_segs(px, py, segs)
    ds = _sdf_segs(px - 0.015, py + 0.015, segs)
    shad = np.clip(1.0 - (ds - 0.025) / 0.014, 0.0, 1.0)
    fg = np.clip(1.0 - (d - 0.025) / 0.012, 0.0, 1.0)
    ctx.rgb[...] = ctx.rgb * (1.0 - 0.40 * shad[..., None])
    ctx.rgb[...] = ctx.rgb * (1.0 - fg[..., None]) + np.array([58, 52, 46], np.float32) * fg[..., None]
    ctx.height += fg * 1.6
    ctx.gloss[...] = np.where(fg > 0.3, 0.58, ctx.gloss)


def paint_pier_num(ctx, w_m=1.40, h_m=1.10):
    granite(ctx, 2, 1, 0.14, 3.5, 0.14)
    px, py = ctx.u * w_m, ctx.v * h_m
    segs = _num_segs(w_m * 0.50, h_m * 0.30, 0.25, 0.42, DONG)
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


TEX = {
    "stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 3, 0.3, 7.0, 0.12)),
    "maroon": dict(tile=(2.4, FH), px=512, painter=lambda c: granite(c, 2, 3, 0.18, 3.0)),
    "pale": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 3, 0.12, 2.5)),
    "grey_stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 3, 0.18, 4.0)),
    "travertine": dict(tile=(5.85, 1.55), px=512, painter=lambda c: granite(c, 3, 1, 0.12, 2.5, 0.10)),
    "ent_lintel": dict(tile=(5.85, 0.84), px=512, painter=paint_ent_lintel),
    "window": dict(px=2048, painter=window_glass, emissive=(255, 205, 150)),
    "vent_glass": dict(px=256, painter=hopper_vent),
    "pier_pink": dict(tile=(1.40, 1.10), px=512, painter=lambda c: granite(c, 2, 1, 0.14, 3.5, 0.14)),
    "pier_course": dict(tile=(0.60, 1.2), px=256, painter=paint_pier_course),
    "pier_num": dict(tile=(1.40, 1.10), px=512, painter=paint_pier_num),
    "roof": dict(tile=(4.0, 4.0), px=512, painter=roofing),
    "canopy": dict(tile=(1.2, 1.2), px=256, painter=lambda c: paving(c, 2)),
    "louver": dict(tile=(0.6, 2.05), px=256, painter=shutter),
    "clerestory": dict(tile=(0.85, 0.64), px=128, painter=clerestory, emissive=(255, 232, 196)),
    "vestibule": dict(px=1024, painter=vestibule, emissive=(255, 226, 184)),
    "rev_glass": dict(tile=(0.45, 0.45), px=128, painter=rev_glass, emissive=(255, 226, 184)),
    "stainless": dict(tile=(0.45, 0.45), px=128, painter=brushed_stainless),
    "crown_white": dict(tile=(0.6, 0.6), px=128, painter=lambda c: c.grain(amp=2.0, scale_px=2, height=0.2, seed=19)),
    "fan_grille": dict(px=128, painter=fan_grille),
    "soffit": dict(tile=(1.2, 1.2), px=256, painter=soffit, emissive=(255, 226, 184)),
    "soil": dict(tile=(1.2, 1.2), px=128, painter=soil),
    "foliage": dict(tile=(1.2, 1.2), px=256, painter=foliage),
    "ent_light": dict(px=32, painter=flat_emis(0.28), emissive=(255, 218, 155)),
    "obst_light": dict(px=32, painter=flat_emis(0.6), emissive=(255, 58, 40)),
}

A = K.Atlas(size=4096, pad=16)
for name, color, metal, gloss, px in (
        ("stone", (54, 60, 72), 0.0, 0.35, 128),           # photo 155809: blue-charcoal granite (#374762 zone)
        ("stone_trim", (50, 56, 66), 0.0, 0.35, 64),
        ("pale", (226, 228, 226), 0.0, 0.3, 128),
        ("maroon", (96, 48, 54), 0.0, 0.3, 128),
        ("travertine", (198, 188, 174), 0.0, 0.35, 128),
        ("ent_lintel", (198, 188, 174), 0.0, 0.35, 512),
        ("crown_white", (232, 233, 230), 0.1, 0.4, 64),
        ("railing", (200, 203, 205), 0.6, 0.5, 64),
        ("frame", (218, 222, 225), 0.3, 0.5, 64),
        ("louver", (230, 231, 229), 0.2, 0.4, 64),
        ("roof", (120, 122, 122), 0.0, 0.3, 64),
        ("pier_pink", (190, 150, 140), 0.0, 0.4, 128),
        ("pier_course", (196, 166, 156), 0.0, 0.35, 256),
        ("pier_num", (190, 150, 140), 0.0, 0.45, 512),
        ("canopy", (160, 163, 162), 0.2, 0.45, 128),
        ("grey_stone", (168, 168, 164), 0.0, 0.3, 128),
        ("clerestory", (44, 58, 66), 0.5, 0.9, 128),
        ("vestibule", (46, 62, 66), 0.3, 0.9, 1024),
        ("rev_glass", (38, 66, 72), 0.45, 0.9, 128),
        ("stainless", (212, 216, 220), 0.78, 0.82, 128),
        ("fan_grille", (78, 82, 88), 0.45, 0.55, 128),
        ("soffit", (206, 208, 204), 0.0, 0.3, 256),
        ("soil", (72, 54, 40), 0.0, 0.15, 64),
        ("foliage", (56, 94, 48), 0.0, 0.2, 128),
        ("ent_light", (248, 224, 176), 0.0, 0.5, 32),
        ("obst_light", (226, 62, 50), 0.0, 0.6, 32),
        ("vent_glass", (48, 84, 106), 0.0, 0.78, 256),
        ("window", (70, 110, 110), 0.0, 0.9, 1024)):
    A.add(name, color=color, ctrl=(0, 0, 0), metal=metal, gloss=gloss, **dict(dict(px=px), **TEX.get(name, {})))

WS = K.WindowSet()
LIT_CELLS = 7


def window(mb, stage, axis, c, s, a0, a1, z0, z1, floor, unit, mull=(0.38,), jambs=(True, True)):
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
        zt = z0 + 0.44 * (z1 - z0)             # lower transom bar (~44% height from sill, photo 155809)
        K.paint(mb, axis, c, s, a0, a1, zt - 0.025, zt + 0.025, "frame", layer=lm + 1)
        if mull == QUAD:
            # Two upper centre hopper/awning vent sashes (photos 155809/155129); clears centre/corner rays
            for u0, u1 in ((0.36, 0.47), (0.53, 0.64)):
                xa0 = a0 + (a1 - a0) * u0 + 0.03
                xa1 = a0 + (a1 - a0) * u1 - 0.03
                K.paint(mb, axis, c, s, xa0, xa1, zt + 0.025, z1, "vent_glass", layer=lm)


def louver(mb, stage, axis, c, s, a0, a1, z0, z1):
    if stage == 0:
        K.axbox(mb, axis, c, s, a0, a1, 0, 0.08, z0, z1, "louver")


TRIPLE = (0.33, 0.67)
QUAD = (0.36, 0.47, 0.53, 0.64)            # asymmetric 4-pane wing window (photo 155809); centre pair clears ray-check
PAIR_LN = (0.62,)
PAIR_RN = (0.38,)
HALF = (0.42, 0.58)                           # twin-pane leaving centre u=0.50 clear for ray-check
CW = 0.15

PALE_F = 5                                    # dark granite podium below storey 5, pale stone above (photo 155809)

# ------------------------------------------------------------------------------
# PLAN from the OpenStreetMap footprint of the B-type towers (ways 934368139/40/37/38 = 101/104/109/112,
# 29.7 x 22.8 m).  Front outer dark/maroon bays set back 1.0 m behind the inner pale wings (photo 155809);
# rear has a 4.4 m x 2.3 m recessed core slot (photo 155146).  Walls and disjoint roof rects are built
# directly from the closed CCW outline so there are no coplanar paint overhangs or roof seam lines.
# ------------------------------------------------------------------------------
RW, RD = 1.5, 4.5                             # front recess half width / depth
NX = 5.35                                     # outer front bays (dark left / maroon right) -- photo 155809
XW = X - NX                                   # 9.50 m inner wing outer edge
OUTER_Y0 = 1.00                               # outer front bays step-back from y=0.0
DK_EDGE = 1.10                                # full-height dark granite vertical reveal bordering front slot
RW_B, RD_B = 2.20, 2.30                       # rear central slot half width / depth (photo 155146)

# (p0, p1, axis, c, s, a0, a1, kind, tone, spans_override_or_None)
# Continuous CCW perimeter segments; front/side/rear walls carry explicit window/louver specs.
WIN_QUADS = {
    ("front_l_outer",): ((-X + 1.05, -X + 3.45, PAIR_LN), (-X + 3.85, -X + NX - 0.30, HALF)),
    ("front_l_wing",): ((-XW + 1.65, -RW - 1.10, QUAD),),
    ("front_r_wing",): ((RW + 1.10, XW - 1.65, QUAD),),
    ("front_r_outer",): ((XW + 0.30, XW + 1.50, HALF), (XW + 1.90, X - 1.05, PAIR_RN)),
    ("front_recess",): ((-RW + 0.40, RW - 0.40, TRIPLE),),
    ("rear_l_wing",): ((-8.90, -3.50, QUAD),),
    ("rear_r_wing",): ((3.40, 6.20, TRIPLE), (6.70, 9.00, PAIR_RN)),
    ("rear_recess_l",): ((-1.85, -0.30, PAIR_LN),),
    ("rear_recess_r",): ((0.30, 1.85, PAIR_RN),),
    ("side_outer",): ((1.75, 4.05, PAIR_RN), (4.45, 6.25, HALF)),
    ("side_s1",): ((7.65, 10.25, TRIPLE),),
    ("side_s2",): ((11.45, 13.05, HALF),),
    ("side_s3",): ((14.25, 16.75, TRIPLE),),
    ("side_s4",): ((18.10, 20.40, PAIR_RN),),
}

# CCW vertices paired with upper wall tone (>= PALE_F) and explicit feature role
# Each item: (vx, vy, tone_to_next, tag) where tag in ("win", "slot", "wall", "louver_step")
_PERIM_SPEC = (
    (-X, OUTER_Y0, "stone", "front_l_outer"),
    (-XW, OUTER_Y0, "pale", "wall"),
    (-XW, 0.0, "pale", "front_l_wing"),
    (-RW - DK_EDGE, 0.0, "stone", "wall"),
    (-RW, 0.0, "stone", "slot"),
    (-RW, RD, "stone", "front_recess"),
    (RW, RD, "stone", "slot"),
    (RW, 0.0, "stone", "wall"),
    (RW + DK_EDGE, 0.0, "pale", "front_r_wing"),
    (XW, 0.0, "pale", "wall"),
    (XW, OUTER_Y0, "maroon", "front_r_outer"),
    (X, OUTER_Y0, "maroon", "side_outer"),          # maroon wraps onto +X outer bay (photo 155129)
    (X, 7.0, "stone", "louver_step"),
    (11.6, 7.0, "pale", "side_s1"),
    (11.6, 10.9, "stone", "wall"),
    (9.4, 10.9, "stone", "side_s2"),
    (9.4, 13.6, "stone", "louver_step"),
    (11.8, 13.6, "pale", "side_s3"),
    (11.8, 17.4, "pale", "wall"),
    (10.2, 17.4, "pale", "side_s4"),
    (10.2, D, "pale", "rear_r_wing"),
    (RW_B, D, "grey_stone", "wall"),
    (RW_B, D - RD_B, "grey_stone", "rear_recess_r"),
    (0.0, D - RD_B, "stone", "rear_recess_l"),
    (-RW_B, D - RD_B, "pale", "wall"),
    (-RW_B, D, "pale", "rear_l_wing"),
    (-10.2, D, "pale", "side_s4"),
    (-10.2, 17.4, "pale", "wall"),
    (-11.8, 17.4, "pale", "side_s3"),
    (-11.8, 13.6, "stone", "louver_step"),
    (-9.4, 13.6, "stone", "side_s2"),
    (-9.4, 10.9, "stone", "wall"),
    (-11.6, 10.9, "pale", "side_s1"),
    (-11.6, 7.0, "stone", "louver_step"),
    (-X, 7.0, "stone", "side_outer"),
)

# Disjoint roof rectangles partitioning the exact interior of _PERIM_SPEC at z = H
ROOF_RECTS = (
    (-X, -XW, OUTER_Y0, 7.0),
    (-XW, -RW, 0.0, RD),
    (RW, XW, 0.0, RD),
    (XW, X, OUTER_Y0, 7.0),
    (-XW, XW, RD, 7.0),
    (-11.6, 11.6, 7.0, 10.9),
    (-9.4, 9.4, 10.9, 13.6),
    (-11.8, 11.8, 13.6, 17.4),
    (-10.2, 10.2, 17.4, D - RD_B),
    (-10.2, -RW_B, D - RD_B, D),
    (RW_B, 10.2, D - RD_B, D),
)


def _perimeter_edges():
    """Return list of dicts describing every CCW boundary edge, its orientation, and corner types."""
    pts = [(v[0], v[1]) for v in _PERIM_SPEC]
    n = len(pts)

    def _corner_turn(i):
        a, p, b = pts[i - 1], pts[i], pts[(i + 1) % n]
        cr = (p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0])
        return 1 if cr > 1e-6 else (-1 if cr < -1e-6 else 0)

    conv = [_corner_turn(i) for i in range(n)]
    edges = []
    for i in range(n):
        j = (i + 1) % n
        (x0, y0), (x1, y1) = pts[i], pts[j]
        tone, tag = _PERIM_SPEC[i][2], _PERIM_SPEC[i][3]
        if abs(y1 - y0) < 1e-9:
            axis, c, s = "y", y0, (-1 if x1 > x0 else 1)
            a0, a1 = min(x0, x1), max(x0, x1)
            c0, c1 = (conv[i], conv[j]) if x1 > x0 else (conv[j], conv[i])
        else:
            axis, c, s = "x", x0, (1 if y1 > y0 else -1)
            a0, a1 = min(y0, y1), max(y0, y1)
            c0, c1 = (conv[i], conv[j]) if y1 > y0 else (conv[j], conv[i])
        edges.append(dict(p0=(x0, y0), p1=(x1, y1), axis=axis, c=c, s=s,
                          a0=a0, a1=a1, c0=c0, c1=c1, tone=tone, tag=tag))
    return edges


EDGES = _perimeter_edges()

# Explicit 1F window spans separating ground lobby/residential windows from residential upper storeys
FRONT_1F_SPANS = {
    "front_l_outer": ((-14.10, -11.95, PAIR_LN),),
    "front_recess": ((-1.05, 1.05, PAIR_RN),),
    "front_r_wing": ((2.90, 5.15, PAIR_LN), (6.05, 8.30, PAIR_RN)),
    "front_r_outer": ((10.75, 13.65, TRIPLE),),
}


def ledges(mb, stage):
    """Per-floor horizontal ledges & podium/roof cornices as mitered outward loops (zero z-fighting)."""
    pts = [v[:2] for v in _PERIM_SPEC]
    n = len(pts)
    nrms = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        L = math.hypot(x1 - x0, y1 - y0)
        nrms.append(((y1 - y0) / L, -(x1 - x0) / L))  # unit outward normal of CCW perimeter

    def _miter_pts(d):
        out = []
        for i in range(n):
            n0, n1 = nrms[i - 1], nrms[i]
            denom = 1.0 + n0[0] * n1[0] + n0[1] * n1[1]
            out.append((pts[i][0] + (n0[0] + n1[0]) / denom * d, pts[i][1] + (n0[1] + n1[1]) / denom * d))
        return out

    def _emit_ring(z0, z1, d, mat_fn):
        Q = _miter_pts(d)
        for i, e in enumerate(EDGES):
            mat = mat_fn(e)
            if not mat:
                continue
            j = (i + 1) % n
            (px0, py0), (px1, py1) = pts[i], pts[j]
            (qx0, qy0), (qx1, qy1) = Q[i], Q[j]
            uv = A.uv(mat)
            mb.rect([(qx0, qy0, z0), (qx1, qy1, z0), (qx1, qy1, z1), (qx0, qy0, z1)], mat)
            mb.quad([(qx0, qy0, z1), (qx1, qy1, z1), (px1, py1, z1), (px0, py0, z1)], uv, mat)
            mb.quad([(px0, py0, z0), (px1, py1, z0), (qx1, qy1, z0), (qx0, qy0, z0)], uv, mat)

    def _emit_1f_belt(z0, z1, d):
        Q = _miter_pts(d)
        # Skip edges occluded by entrance portico / right 1F colonnade
        skip_tags = {"front_l_wing", "front_r_outer"}
        for i, e in enumerate(EDGES):
            tag = e["tag"]
            if tag in skip_tags or (tag == "wall" and abs(e["c"] - XW) < 0.05) or (
                    tag == "wall" and abs(e["c"]) < 0.05 and e["p0"][0] < -RW):
                continue
            j = (i + 1) % n
            (px0, py0), (px1, py1) = pts[i], pts[j]
            (qx0, qy0), (qx1, qy1) = Q[i], Q[j]
            if tag == "front_l_outer":
                # Keep only left exposed span (-14.85 .. -11.75), flush-capped at -11.75
                px1, py1 = -11.75, OUTER_Y0
                qx1, qy1 = -11.75, OUTER_Y0 - d
                mb.rect([(qx1, qy1, z0), (px1, py1, z0), (px1, py1, z1), (qx1, qy1, z1)], "stone_trim")
            elif tag == "front_r_wing":
                # Flush stop at x = XW before 1F colonnade
                qx1, qy1 = XW, -d
                mb.rect([(qx1, qy1, z0), (px1, py1, z0), (px1, py1, z1), (qx1, qy1, z1)], "stone_trim")
            elif tag == "wall" and abs(e["c"] - X) < 0.05 and e["p0"][1] < 0.5:
                continue
            elif tag == "side_outer" and e["p0"][0] > 0:
                qx0, qy0 = X + d, OUTER_Y0
                mb.rect([(px0, py0, z0), (qx0, qy0, z0), (qx0, qy0, z1), (px0, py0, z1)], "stone_trim")
            uv = A.uv("stone_trim")
            mb.rect([(qx0, qy0, z0), (qx1, qy1, z0), (qx1, qy1, z1), (qx0, qy0, z1)], "stone_trim")
            mb.quad([(qx0, qy0, z1), (qx1, qy1, z1), (px1, py1, z1), (px0, py0, z1)], uv, "stone_trim")
            mb.quad([(px0, py0, z0), (px1, py1, z0), (qx1, qy1, z0), (qx0, qy0, z0)], uv, "stone_trim")

    if stage < 2:
        _emit_1f_belt(GH - 0.26, GH, 0.20)
        _emit_ring(zf(PALE_F) - 0.16, zf(PALE_F), 0.14, lambda e: "stone_trim")
        _emit_ring(H - 0.26, H, 0.24, lambda e: "stone" if e["tag"] in ("slot", "front_recess") else "pale")
    if stage == 0:
        for f in range(PALE_F + 1, NF):
            z = zf(f)
            _emit_ring(z - LEDGE_T, z, LEDGE_P, lambda e: e["tone"])


def facade_floor(mb, stage, f, skip=None):
    """All windows and slot louvers of storey f; f==0 separates 1F residential glazing from upper floors."""
    z = zf(f)
    u = 0
    for e in EDGES:
        axis, c, s, a0, a1, tag = e["axis"], e["c"], e["s"], e["a0"], e["a1"], e["tag"]
        if tag == "slot":
            if f > 0:
                louver(mb, stage, axis, c, s, 1.4, 2.8, z + 0.45, z + HEAD)
            continue
        if tag == "louver_step":
            if f > 0 and a1 - a0 >= 1.8:
                mid = (a0 + a1) / 2
                louver(mb, stage, axis, c, s, mid - 0.55, mid + 0.55, z + 0.45, z + HEAD)
            continue
        if tag == "wall":
            continue

        if f == 0:
            if tag in FRONT_1F_SPANS:
                for b0, b1, mull in FRONT_1F_SPANS[tag]:
                    if skip and axis == "y" and c <= OUTER_Y0 + 0.05 and b1 > skip[0] and b0 < skip[1]:
                        continue
                    z0, z1 = (0.45, 3.65) if tag == "front_r_outer" else (1.85, 3.60)
                    window(mb, stage, axis, c, s, b0, b1, z0, z1, f, u, mull); u += 1
            elif tag in ("side_outer", "side_s1", "side_s2", "side_s3", "side_s4", "rear_l_wing", "rear_r_wing"):
                for b0, b1, mull in WIN_QUADS.get((tag,), ()):
                    window(mb, stage, axis, c, s, b0, b1, 1.65, 3.60, f, u, mull); u += 1
            continue

        z0, z1 = z + SILL, z + HEAD
        for b0, b1, mull in WIN_QUADS.get((tag,), ()):
            if skip and axis == "y" and c <= OUTER_Y0 + 0.05 and b1 > skip[0] and b0 < skip[1]:
                continue
            window(mb, stage, axis, c, s, b0, b1, z0, z1, f, u, mull); u += 1
        if tag == "side_s4":
            louver(mb, stage, axis, c, s, 20.90, 22.00, z + 0.45, z1)


def prism(mb, p0, p1, w, region):
    d = [b - a for a, b in zip(p0, p1)]
    L = math.sqrt(sum(v * v for v in d))
    if L < 1e-6:
        return
    t = [v / L for v in d]
    u = [1.0, 0.0, 0.0] if abs(t[0]) < 1e-6 and abs(t[1]) < 1e-6 else [t[1], -t[0], 0.0]
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
# FLAT SEGMENTED ROOF: parapets on every slab edge, core stair/lift penthouse, small plant boxes.
# Aerial shows no helipad marking on any B-type tower.
# ==============================================================================
PT = 0.35                                     # parapet thickness
PH = H + 1.4                                  # parapet top
PHC = PH + 0.14                               # overhanging coping cap top


def outline():
    """Roof outline (non-collinear CCW vertices) derived directly from _PERIM_SPEC."""
    pts = [(v[0], v[1]) for v in _PERIM_SPEC]
    keep = []
    n = len(pts)
    for i, p in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % n]
        if abs((p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0])) > 1e-6:
            keep.append(p)
    return keep


def _cyl_z(mb, cx, cy, r, z0, z1, segs, region, cap_top=True, cap_bot=False):
    """Closed vertical N-gon prism centered at (cx, cy) from z0 to z1."""
    pts = [(cx + r * math.cos(2 * math.pi * k / segs), cy + r * math.sin(2 * math.pi * k / segs))
           for k in range(segs + 1)]
    for k in range(segs):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        mb.rect([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], region)
        if cap_top:
            mb.tri([(cx, cy, z1), (x0, y0, z1), (x1, y1, z1)], A.uv(region)[:3], region)
        if cap_bot:
            mb.tri([(cx, cy, z0), (x1, y1, z0), (x0, y0, z0)], A.uv(region)[:3], region)


def _parapet_curb(mb, x0, x1, y0, y1, z_deck, h_curb, t=0.24, wall_mat="crown_white",
                  cap_mat="crown_white", deck_mat="roof"):
    """Disjoint perimeter parapet curb + overhanging coping cap enclosing a recessed roof membrane."""
    zt = z_deck + h_curb
    K.floor_quad(mb, x0 + t, x1 - t, y0 + t, y1 - t, z_deck, deck_mat)
    # Four disjoint curb walls around the recessed deck
    mb.box(x0, x1, y0, y0 + t, z_deck, zt, wall_mat, skip=("bottom", "top"))
    mb.box(x0, x1, y1 - t, y1, z_deck, zt, wall_mat, skip=("bottom", "top"))
    mb.box(x0, x0 + t, y0 + t, y1 - t, z_deck, zt, wall_mat, skip=("bottom", "top", "front", "back"))
    mb.box(x1 - t, x1, y0 + t, y1 - t, z_deck, zt, wall_mat, skip=("bottom", "top", "front", "back"))
    # Projecting metal coping cap lip above the curb wall (zero overlap with wall top)
    ov, zc = 0.04, zt + 0.08
    mb.box(x0 - ov, x1 + ov, y0 - ov, y0 + t + ov, zt, zc, cap_mat)
    mb.box(x0 - ov, x1 + ov, y1 - t - ov, y1 + ov, zt, zc, cap_mat)
    mb.box(x0 - ov, x0 + t + ov, y0 + t + ov, y1 - t - ov, zt, zc, cap_mat, skip=("front", "back"))
    mb.box(x1 - t - ov, x1 + ov, y0 + t + ov, y1 - t - ov, zt, zc, cap_mat, skip=("front", "back"))


def _roof_vent(mb, cx, cy, z_base, r=0.35):
    """Mounted rooftop concrete curb + stainless riser + rotary turbine vent + crown cap."""
    mb.box(cx - 0.42, cx + 0.42, cy - 0.42, cy + 0.42, z_base, z_base + 0.14, "grey_stone", skip=("bottom",))
    _cyl_z(mb, cx, cy, r * 0.62, z_base + 0.14, z_base + 0.42, 8, "stainless", cap_top=False)
    _cyl_z(mb, cx, cy, r, z_base + 0.42, z_base + 0.64, 8, "louver", cap_top=True, cap_bot=True)
    _cyl_z(mb, cx, cy, r * 0.72, z_base + 0.64, z_base + 0.72, 8, "crown_white", cap_top=True)


def _hooded_door(mb, axis, c, s, a_mid, z_base, w=1.10, h=2.05):
    """Rooftop steel access door with stainless casing trim and cantilevered rain hood."""
    a0, a1 = a_mid - w / 2, a_mid + w / 2
    K.paint(mb, axis, c, s, a0, a1, z_base + 0.05, z_base + h, "stone_trim", layer=2)
    K.paint(mb, axis, c, s, a0 - 0.06, a0, z_base + 0.05, z_base + h + 0.06, "stainless", layer=3)
    K.paint(mb, axis, c, s, a1, a1 + 0.06, z_base + 0.05, z_base + h + 0.06, "stainless", layer=3)
    K.axbox(mb, axis, c, s, a0 - 0.12, a1 + 0.12, 0.0, 0.24, z_base + h, z_base + h + 0.10, "crown_white")


def parapet_ring(mb, stage):
    """One continuous mitred parapet + projecting coping overhang lip on stage < 2."""
    P = outline()
    n = len(P)

    def inward(a, b):                         # left normal of edge a->b (inside for a CCW outline)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        return -dy / L, dx / L

    Q = []
    Po = []
    Qo = []
    for i in range(n):
        n0, n1 = inward(P[i - 1], P[i]), inward(P[i], P[(i + 1) % n])
        nx, ny = n0[0] + n1[0], n0[1] + n1[1]
        Q.append((P[i][0] + nx * PT, P[i][1] + ny * PT))
        Po.append((P[i][0] - nx * 0.05, P[i][1] - ny * 0.05))
        Qo.append((P[i][0] + nx * (PT + 0.04), P[i][1] + ny * (PT + 0.04)))
    uv = A.uv("crown_white")
    uv_trim = A.uv("stone_trim")
    for i in range(n):
        j = (i + 1) % n
        (ax, ay), (bx, by), (cx, cy), (dx, dy) = P[i], P[j], Q[j], Q[i]
        in_slot = abs(ax) <= RW + 0.05 and abs(bx) <= RW + 0.05 and ay <= RD + 0.05 and by <= RD + 0.05 and max(ay, by) >= 0.5
        out_mat = "stone" if in_slot else "pale"
        mb.rect([(ax, ay, H), (bx, by, H), (bx, by, PH), (ax, ay, PH)], out_mat)     # outer face
        mb.rect([(cx, cy, H), (dx, dy, H), (dx, dy, PH), (cx, cy, PH)], "grey_stone")  # inner face
        if stage == 2:
            mb.quad([(ax, ay, PH), (bx, by, PH), (cx, cy, PH), (dx, dy, PH)], uv, "crown_white")
        else:
            (axo, ayo), (bxo, byo), (cxo, cyo), (dxo, dyo) = Po[i], Po[j], Qo[j], Qo[i]
            mb.rect([(axo, ayo, PH), (bxo, byo, PH), (bxo, byo, PHC), (axo, ayo, PHC)], "crown_white")
            mb.rect([(cxo, cyo, PH), (dxo, dyo, PH), (dxo, dyo, PHC), (cxo, cyo, PHC)], "crown_white")
            mb.quad([(axo, ayo, PHC), (bxo, byo, PHC), (cxo, cyo, PHC), (dxo, dyo, PHC)], uv, "crown_white")
            # Downward overhang soffits outside [P..Q] (no coplanar contact with parapet wall top)
            mb.quad([(ax, ay, PH), (bx, by, PH), (bxo, byo, PH), (axo, ayo, PH)], uv_trim, "stone_trim")
            mb.quad([(cxo, cyo, PH), (dxo, dyo, PH), (dx, dy, PH), (cx, cy, PH)], uv_trim, "stone_trim")


def roof(mb, stage):
    parapet_ring(mb, stage)
    if stage == 2:
        # Simplified single-block penthouse silhouette for LOD2 (keeps <= 500 tris)
        mb.box(-4.5, 4.5, 7.2, 20.4, H, H + 4.3, dict(top="roof", default="pale"), skip=("bottom",))
        return
    # Twin spine & double-court central penthouse matching aerial roof photos
    if stage == 1:
        mb.box(-4.5, -2.7, 7.2, 22.3, H, H + 4.3, dict(top="roof", default="pale"), skip=("bottom",))
        mb.box(2.7, 4.5, 7.2, 22.3, H, H + 4.3, dict(top="roof", default="pale"), skip=("bottom",))
    else:
        for sx0, sx1 in ((-4.5, -2.7), (2.7, 4.5)):
            mb.box(sx0, sx1, 7.2, 22.3, H, H + 4.10, "pale", skip=("bottom", "top"))
            _parapet_curb(mb, sx0, sx1, 7.2, 22.3, H + 4.10, 0.36, t=0.22, wall_mat="pale")
    for y0, y1, h_top, mat in ((7.2, 8.8, 3.9, "crown_white"),
                               (13.9, 15.3, 3.9, "crown_white"),
                               (19.0, 20.4, 4.1, "pale")):
        if stage == 1:
            mb.box(-2.7, 2.7, y0, y1, H, H + h_top, dict(top="roof", default=mat), skip=("bottom", "left", "right"))
        else:
            mb.box(-2.7, 2.7, y0, y1, H, H + h_top - 0.24, mat, skip=("bottom", "top", "left", "right"))
            K.floor_quad(mb, -2.7, 2.7, y0 + 0.22, y1 - 0.22, H + h_top - 0.24, "roof")
            for cy0, cy1 in ((y0, y0 + 0.22), (y1 - 0.22, y1)):
                mb.box(-2.7, 2.7, cy0, cy1, H + h_top - 0.24, H + h_top + 0.06, "crown_white",
                       skip=("bottom", "left", "right"))
    for y0, y1 in ((8.8, 13.9), (15.3, 19.0)):
        mb.box(-0.55, 0.55, y0, y1, H, H + 3.5, dict(top="roof", default="grey_stone"),
               skip=("bottom", "front", "back"))
    # Front wing stairwell overruns
    for x0, x1 in ((-12.6, -8.4), (8.4, 12.6)):
        if stage == 1:
            mb.box(x0, x1, 2.0, 5.8, H, H + 2.2, dict(top="roof", default="crown_white"), skip=("bottom",))
        else:
            mb.box(x0, x1, 2.0, 5.8, H, H + 2.05, "crown_white", skip=("bottom", "top"))
            _parapet_curb(mb, x0, x1, 2.0, 5.8, H + 2.05, 0.30, t=0.24)
    # Rear wing HVAC enclosures (multi-tier plinth + framed louver bay + fan cowlings on stage 0)
    for x0, x1 in ((-8.6, -5.8), (5.8, 8.6)):
        if stage == 1:
            mb.box(x0, x1, 18.0, 20.6, H, H + 1.4, dict(top="louver", default="grey_stone"), skip=("bottom",))
        else:
            mb.box(x0, x1, 18.0, 20.6, H, H + 0.24, "grey_stone", skip=("bottom",))
            mb.box(x0 + 0.08, x1 - 0.08, 18.08, 20.52, H + 0.24, H + 1.54,
                   dict(top="stainless", default="louver"), skip=("bottom",))
            for cx_p in (x0 + 0.14, x1 - 0.14):
                for cy_p in (18.14, 20.46):
                    mb.box(cx_p - 0.10, cx_p + 0.10, cy_p - 0.10, cy_p + 0.10,
                           H + 0.24, H + 1.54, "crown_white", skip=("bottom", "top"))
            mb.box(x0 - 0.04, x1 + 0.04, 17.96, 20.64, H + 1.54, H + 1.68, "crown_white")
            xc_mid = (x0 + x1) / 2
            for fx in (xc_mid - 0.68, xc_mid + 0.68):
                _cyl_z(mb, fx, 19.3, 0.44, H + 1.68, H + 2.02, 10, "stainless", cap_top=False)
                _cyl_z(mb, fx, 19.3, 0.44, H + 2.02, H + 2.04, 10, "fan_grille", cap_top=True)
    if stage == 0:
        # Penthouse louvers, structural pilasters, hooded maintenance doors & coping trims
        for sx in (-4.5, 4.5):
            s = -1 if sx < 0 else 1
            for py in (8.6, 12.6, 15.6, 20.8):
                mb.box(sx - (0.09 if s < 0 else 0.0), sx + (0.09 if s > 0 else 0.0),
                       py - 0.16, py + 0.16, H, H + 4.10, "pale", skip=("bottom",))
            for y0, y1 in ((9.4, 12.0), (16.0, 18.4)):
                louver(mb, stage, "x", sx, s, y0, y1, H + 1.2, H + 3.4)
        for rx0, rx1 in ((-4.2, -3.0), (3.0, 4.2)):
            louver(mb, stage, "y", 22.3, 1, rx0, rx1, H + 1.3, H + 3.4)
        _hooded_door(mb, "y", 7.2, -1, 0.0, H)
        for sx in (-10.5, 10.5):
            _hooded_door(mb, "y", 5.8, 1, sx, H)
            louver(mb, stage, "y", 2.0, -1, sx - 1.1, sx + 1.1, H + 0.6, H + 1.8)
            mb.box(sx - 1.22, sx + 1.22, 1.94, 2.0, H + 1.80, H + 1.90, "crown_white")
        # Overhead stainless duct runs linking penthouse spines to rear wing HVAC units
        for sign_x, dx0, dx1 in ((-1, -5.8, -4.5), (1, 4.5, 5.8)):
            xm = (dx0 + dx1) / 2
            mb.box(xm - 0.18, xm + 0.18, 19.05, 19.85, H, H + 0.90, "grey_stone", skip=("bottom",))
            mb.box(dx0, dx1, 19.15, 19.75, H + 0.90, H + 1.48, "stainless")
        # Front wing stair overrun rotary ventilators & glazed smoke hatches
        for vx, vy in ((-11.35, 3.15), (-9.55, 4.55), (11.35, 3.15), (9.55, 4.55)):
            _roof_vent(mb, vx, vy, H + 2.05)
        for hx in (-11.35, 9.55):
            hy = 4.55 if hx < 0 else 3.15
            mb.box(hx - 0.55, hx + 0.55, hy - 0.45, hy + 0.45, H + 2.05, H + 2.26, "grey_stone", skip=("bottom",))
            mb.box(hx - 0.48, hx + 0.48, hy - 0.38, hy + 0.38, H + 2.26, H + 2.34, "clerestory", skip=("bottom",))
        # Twin penthouse spine ventilators, HVAC condensers & court guardrails
        for sx in (-3.6, 3.6):
            for vy in (9.6, 17.8):
                _roof_vent(mb, sx, vy, H + 4.10)
            mb.box(sx - 0.52, sx + 0.52, 13.0, 14.4, H + 4.10, H + 4.72,
                   dict(top="fan_grille", default="crown_white"), skip=("bottom",))
            mb.box(sx - 0.56, sx + 0.56, 12.96, 14.44, H + 4.66, H + 4.76, "stainless")
            # Slim lightning / telecom masts at front of penthouse spines (top ~113.4 m)
            _cyl_z(mb, sx, 7.65, 0.055, H + 4.54, H + 5.40, 8, "stainless", cap_top=True)
            mb.box(sx - 0.22, sx + 0.22, 7.62, 7.68, H + 5.18, H + 5.23, "stainless")
        for y0, y1 in ((8.85, 13.85), (15.35, 18.95)):
            for gx in (-0.49, 0.49):
                for py in (y0 + 0.15, (y0 + y1) / 2, y1 - 0.15):
                    prism(mb, (gx, py, H + 3.50), (gx, py, H + 4.42), 0.045, "stainless")
                for dz in (0.45, 0.88):
                    prism(mb, (gx, y0 + 0.15, H + 3.50 + dz), (gx, y1 - 0.15, H + 3.50 + dz), 0.032, "stainless")
        # Pedestal-mounted corner & penthouse aviation obstruction lights
        for xc, yc in ((-X + 0.22, OUTER_Y0 + 0.22), (X - 0.22, OUTER_Y0 + 0.22), (-10.0, D - 0.22), (10.0, D - 0.22)):
            mb.box(xc - 0.05, xc + 0.05, yc - 0.05, yc + 0.05, PHC, PHC + 0.24, "stainless", skip=("bottom",))
            mb.box(xc - 0.12, xc + 0.12, yc - 0.12, yc + 0.12, PHC + 0.24, PHC + 0.46, "obst_light")
        for xc in (-3.6, 3.6):
            mb.box(xc - 0.06, xc + 0.06, 21.82, 22.12, H + 4.54, H + 4.82, "stainless", skip=("bottom",))
            mb.box(xc - 0.14, xc + 0.14, 21.76, 22.18, H + 4.82, H + 5.10, "obst_light")


# ==============================================================================
# ENTRANCE PORCH & 1F PODIUM COLONNADE
# ==============================================================================
EY = -4.05
EZ0, EZB, EZC, EZT = 3.78, 4.62, 5.33, 5.78
PORTICO_X0, PORTICO_X1 = -X + NX - 2.0, -RW - 0.2  # wide dark left pier (-11.50..-9.50), pink pier (-3.65..-1.70)
LP = 2.0
PIER_X0 = PORTICO_X1 - 1.95
ST_N, ST_R, ST_T = 7, 0.15, 0.36


def _arc_shell(mb, cx, cy, a0, a1, segs, r_in, r_out, z0, z1, out_mat,
               in_mat=None, cap_mat=None, cap_ends=True, cap_top=True, cap_bot=True):
    """Closed curved annular arc solid with verified outward normals (a0 < a1 CCW)."""
    in_m = in_mat or out_mat
    cap_m = cap_mat or out_mat
    pin = [(cx + r_in * math.cos(a0 + (a1 - a0) * k / segs),
            cy + r_in * math.sin(a0 + (a1 - a0) * k / segs)) for k in range(segs + 1)]
    pout = [(cx + r_out * math.cos(a0 + (a1 - a0) * k / segs),
             cy + r_out * math.sin(a0 + (a1 - a0) * k / segs)) for k in range(segs + 1)]
    uv_cap = A.uv(cap_m)
    for k in range(segs):
        (x0i, y0i), (x1i, y1i) = pin[k], pin[k + 1]
        (x0o, y0o), (x1o, y1o) = pout[k], pout[k + 1]
        mb.rect([(x0o, y0o, z0), (x1o, y1o, z0), (x1o, y1o, z1), (x0o, y0o, z1)], out_mat)
        mb.rect([(x1i, y1i, z0), (x0i, y0i, z0), (x0i, y0i, z1), (x1i, y1i, z1)], in_m)
        if cap_top:
            mb.quad([(x0i, y0i, z1), (x0o, y0o, z1), (x1o, y1o, z1), (x1i, y1i, z1)], uv_cap, cap_m)
        if cap_bot:
            mb.quad([(x0o, y0o, z0), (x0i, y0i, z0), (x1i, y1i, z0), (x1o, y1o, z0)], uv_cap, cap_m)
    if cap_ends:
        (x0i, y0i), (x0o, y0o) = pin[0], pout[0]
        (xni, yni), (xno, yno) = pin[-1], pout[-1]
        mb.rect([(x0i, y0i, z0), (x0o, y0o, z0), (x0o, y0o, z1), (x0i, y0i, z1)], cap_m)
        mb.rect([(xno, yno, z0), (xni, yni, z0), (xni, yni, z1), (xno, yno, z1)], cap_m)


def _rot_box(mb, cx, cy, r0, r1, th, ang, z0, z1, region, cap_top=True, cap_bot=True):
    """Closed radial prism blade in XY centered along ray ang from radius r0 to r1."""
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    ht = th / 2
    p00 = (cx + r0 * ux - ht * nx, cy + r0 * uy - ht * ny)
    p10 = (cx + r1 * ux - ht * nx, cy + r1 * uy - ht * ny)
    p11 = (cx + r1 * ux + ht * nx, cy + r1 * uy + ht * ny)
    p01 = (cx + r0 * ux + ht * nx, cy + r0 * uy + ht * ny)
    uv = A.uv(region)
    pts = [p00, p10, p11, p01]
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        mb.rect([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], region)
    if cap_top:
        mb.quad([(p[0], p[1], z1) for p in pts], uv, region)
    if cap_bot:
        mb.quad([(p[0], p[1], z0) for p in (p00, p01, p11, p10)], uv, region)


def _revolving_door(mb, stage, cx, cy, z0, z1, r=1.08):
    """3D open-front stainless drum revolving door w/ fascia crown, mullions, spindle & 3 blades."""
    if stage > 0:
        _arc_shell(mb, cx, cy, math.pi, 2 * math.pi, 6, 0.05, r, z0, z1 - 0.24, "vestibule",
                   cap_mat="stainless", cap_bot=False)
        _arc_shell(mb, cx, cy, math.pi, 2 * math.pi, 6, 0.05, r + 0.04, z1 - 0.24, z1, "stainless", cap_bot=False)
        return
    segs = 12
    zc = z1 - 0.34
    # Brushed stainless drum canopy fascia, upper stepped crown rim & ceiling downlight
    _arc_shell(mb, cx, cy, math.pi, 2 * math.pi, segs, r - 0.16, r + 0.05, zc, z1,
               "stainless", in_mat="stainless", cap_mat="stainless")
    _arc_shell(mb, cx, cy, math.pi, 2 * math.pi, segs, r - 0.12, r + 0.02, z1, z1 + 0.06, "stainless", cap_bot=False)
    mb.box(cx - r - 0.05, cx + r + 0.05, cy, -0.06, zc, z1 + 0.06, "stainless", skip=("front", "back"))
    # Semicircular canopy top roof plate & illuminated entry soffit strictly inside r - 0.16
    pts_top = [(cx + (r - 0.16) * math.cos(math.pi + math.pi * k / segs),
                cy + (r - 0.16) * math.sin(math.pi + math.pi * k / segs)) for k in range(segs + 1)]
    uv_roof = A.uv("roof")[:3]
    uv_sof = A.uv("soffit")[:3]
    for k in range(segs):
        (x0, y0), (x1, y1) = pts_top[k], pts_top[k + 1]
        mb.tri([(cx, cy, z1 + 0.02), (x0, y0, z1 + 0.02), (x1, y1, z1 + 0.02)], uv_roof, "roof")
        mb.tri([(cx, cy, zc), (x1, y1, zc), (x0, y0, zc)], uv_sof, "soffit")
    mb.box(cx - 0.22, cx + 0.22, cy - 0.56, cy - 0.22, zc - 0.02, zc, "ent_light", skip=("top",))
    # Motion sensor housing & crisp red directional emblem at front canopy center (photos 109/112)
    mb.box(cx - 0.16, cx + 0.16, cy - r - 0.09, cy - r - 0.05, z1 - 0.12, z1 - 0.02, "stone_trim", skip=("back",))
    mb.box(cx - 0.09, cx + 0.09, cy - r - 0.07, cy - r - 0.05, zc + 0.08, zc + 0.14, "maroon", skip=("back",))
    # Dark floor threshold pad & curved fixed drum side wings (open front portal 232..308 deg)
    _arc_shell(mb, cx, cy, math.pi, 2 * math.pi, segs, 0.09, r - 0.02, z0, z0 + 0.02, "stone_trim", cap_bot=False)
    mb.box(cx - r, cx + r, cy, -0.06, z0, z0 + 0.02, "stone_trim", skip=("bottom", "front", "back"))
    a_left = (math.radians(182), math.radians(230))
    a_right = (math.radians(310), math.radians(358))
    for a0, a1 in (a_left, a_right):
        _arc_shell(mb, cx, cy, a0, a1, 4, r - 0.06, r + 0.015, z0, z0 + 0.15, "stainless",
                   cap_ends=False, cap_bot=False)
        _arc_shell(mb, cx, cy, a0, a1, 4, r - 0.04, r - 0.01, z0 + 0.15, zc, "rev_glass",
                   cap_ends=False, cap_top=False, cap_bot=False)
        _arc_shell(mb, cx, cy, a0, a1, 4, r - 0.055, r + 0.01, z0 + 1.00, z0 + 1.06, "stainless", cap_ends=False)
    # Vertical brushed stainless stanchion mullions + end piers sealing against y = -0.06
    for deg in (206, 232, 308, 334):
        _rot_box(mb, cx, cy, r - 0.065, r + 0.015, 0.06, math.radians(deg), z0, zc, "stainless",
                 cap_top=False, cap_bot=False)
    for ex in (cx - r - 0.02, cx + r - 0.04):
        mb.box(ex, ex + 0.06, cy - 0.02, -0.06, z0, zc, "stainless", skip=("bottom", "top", "back"))
    # Central stainless spindle shaft & 3 radial visible cross-wing leaves (strictly y <= cy)
    _cyl_z(mb, cx, cy, 0.09, z0 + 0.02, zc, 8, "stainless", cap_top=False)
    for deg in (198, 268, 338):
        ang = math.radians(deg)
        r_leaf = r - 0.16
        _rot_box(mb, cx, cy, 0.09, r_leaf, 0.042, ang, z0 + 0.04, z0 + 0.14, "stainless")
        _rot_box(mb, cx, cy, 0.09, r_leaf, 0.042, ang, zc - 0.10, zc - 0.02, "stainless")
        _rot_box(mb, cx, cy, r_leaf - 0.06, r_leaf, 0.042, ang, z0 + 0.14, zc - 0.10, "stainless",
                 cap_top=False, cap_bot=False)
        _rot_box(mb, cx, cy, 0.09, r_leaf - 0.06, 0.020, ang, z0 + 0.14, zc - 0.10, "rev_glass",
                 cap_top=False, cap_bot=False)
        _rot_box(mb, cx, cy, 0.14, r_leaf - 0.08, 0.058, ang, z0 + 1.00, z0 + 1.05, "stainless")


def _shrubs(mb, cx0, cx1, cy0, cy1, z_base, h_max=0.62):
    """Soil bed + 2-tier mounded botanical shrub hedging inside a stone planter."""
    mb.box(cx0, cx1, cy0, cy1, z_base - 0.04, z_base + 0.03, "soil", skip=("bottom",))
    nx = max(2, int((cx1 - cx0) / 1.15))
    dx = (cx1 - cx0) / nx
    ym = (cy0 + cy1) / 2
    ry = (cy1 - cy0) * 0.38
    for i in range(nx):
        sx0 = cx0 + i * dx + 0.08
        sx1 = cx0 + (i + 1) * dx - 0.08
        h = h_max * (0.72 + 0.28 * ((i * 3 + 1) % 3) / 2.0)
        h_mid = z_base + 0.55 * h
        mb.box(sx0, sx1, ym - ry, ym + ry, z_base + 0.02, h_mid, "foliage", skip=("bottom",))
        mb.box(sx0 + 0.14, sx1 - 0.14, ym - ry * 0.65, ym + ry * 0.65, h_mid, z_base + h, "foliage",
               skip=("bottom",))


def entrance(mb, stage):
    if stage == 2:
        # Simplified portico massing for LOD2
        mb.box(PORTICO_X0, PORTICO_X0 + LP, EY, 0.0, 0, EZT, "stone_trim", skip=("bottom", "back"))
        mb.box(PORTICO_X0 + LP, PIER_X0, EY, 0.0, EZ0, EZT,
               dict(front="travertine", top="roof", default="stone_trim"), skip=("bottom", "back"))
        mb.box(PIER_X0, PORTICO_X1, EY, 0.0, 0, EZT, "pier_pink", skip=("bottom", "back"))
        return

    # Left dark granite pier (base plinth + shaft, cleanly meeting canopy without overlap)
    mb.box(PORTICO_X0 - 0.10, PORTICO_X0 + LP + 0.05, EY - 0.10, EY + 1.20, 0, 0.16, "stone_trim", skip=("bottom",))
    mb.box(PORTICO_X0 - 0.05, PORTICO_X0 + LP, EY - 0.05, EY + 1.15, 0.16, EZC, "stone_trim", skip=("bottom", "top"))
    # Rear beam behind left pier sealing into set-back outer bay at y = OUTER_Y0
    mb.box(PORTICO_X0, PORTICO_X0 + LP, EY + 1.15, OUTER_Y0, EZ0, EZC,
           dict(bottom="soffit", left="stone_trim", default="travertine"), skip=("front", "back", "top"))

    # Center portico canopy beam: lower travertine EXLLU TOWER lintel (EZ0..EZB) + upper clerestory band (EZB..EZC)
    y_beam = EY + 0.35
    mb.box(PORTICO_X0 + LP, PIER_X0, y_beam, 0.0, EZ0, EZB,
           dict(bottom="soffit", default="travertine"), skip=("back", "top", "left", "right", "front"))
    mb.quad(K.face_pts("y", y_beam, -1, PORTICO_X0 + LP, PIER_X0, EZ0, EZB), A.uv_full("ent_lintel"), "ent_lintel")
    mb.box(PORTICO_X0 + LP, PIER_X0, y_beam, 0.0, EZB, EZC,
           dict(front="travertine", default="travertine"), skip=("back", "top", "left", "right", "bottom"))
    mb.box(PIER_X0, PORTICO_X1, EY + 1.90, 0.0, EZ0, EZC,
           dict(front="travertine", right="travertine", bottom="soffit", default="travertine"),
           skip=("back", "top", "left"))

    # Right rose-marble pier: smooth inner bay (gold DONG numerals + sconce) + split-face outer course + slim dark border
    mb.box(PIER_X0 - 0.05, PORTICO_X1 + 0.10, EY - 0.20, EY + 1.95, 0, 0.16, "stone_trim", skip=("bottom",))
    px_mid = PIER_X0 + 1.40
    mb.box(PIER_X0, px_mid, EY - 0.15, EY + 1.65, 0.16, EZC, "pier_pink",
           skip=("bottom", "top", "back", "front", "right"))
    for z0, z1, mat, full in ((0.16, 2.45, "pier_pink", False),
                              (2.45, 3.55, "pier_num", True),
                              (3.55, EZC, "pier_pink", False)):
        pts = K.face_pts("y", EY - 0.15, -1, PIER_X0, px_mid, z0, z1)
        mb.quad(pts, A.uv_full(mat), mat) if full else mb.rect(pts, mat)
    if stage == 0:
        mb.box(PIER_X0 + 0.63, PIER_X0 + 0.77, EY - 0.22, EY - 0.15, 3.60, 3.74,
               dict(bottom="ent_light", default="stone"), skip=("back",))
    mb.box(px_mid, PORTICO_X1 + 0.05, EY - 0.15, EY + 1.65, 0.16, EZC,
           dict(front="pier_course", right="pier_pink", default="pier_pink"),
           skip=("bottom", "top", "back", "left"))
    mb.box(PIER_X0, PORTICO_X1 + 0.05, EY + 1.65, EY + 1.90, 0.16, EZC,
           dict(right="stone_trim", default="pier_pink"), skip=("bottom", "top", "front"))

    # Portico dark granite roof cap crown (plus connector back to OUTER_Y0 over left pier)
    mb.box(PORTICO_X0 - 0.20, PORTICO_X1 + 0.18, EY - 0.22, 0.0, EZC, EZT,
           dict(top="roof", default="stone_trim"), skip=("back",))
    mb.box(PORTICO_X0 - 0.20, PORTICO_X0 + LP, 0.0, OUTER_Y0, EZC, EZT,
           dict(top="roof", default="stone_trim"), skip=("front", "back"))

    # 1F Right outer colonnade framing recessed 1F porch (x = XW..X, y = 0..OUTER_Y0, photo right_1f)
    mb.box(XW, XW + 0.75, 0.0, OUTER_Y0, 0, 3.95, "stone_trim", skip=("bottom", "top", "left", "back"))
    mb.box(X - 0.70, X, 0.0, OUTER_Y0, 0, 3.95, "stone_trim", skip=("bottom", "top", "back"))
    mb.box(XW, X, 0.0, OUTER_Y0, 3.95, GH, dict(top="roof", default="stone_trim"), skip=("back", "left"))
    # 1F Right inner wing pilaster
    mb.box(5.25, 5.95, -0.16, 0.0, 0, GH - 0.26, "stone_trim", skip=("bottom", "top", "back"))

    # Rear entrance canopy (central rear slot y = D - RD_B = 20.50, photo bot_155146)
    yr0, yr1 = D - RD_B, D - RD_B + 1.45
    mb.box(-1.45, -0.95, yr0, yr1 - 0.15, 0, 2.95, "stone_trim", skip=("bottom", "front", "top"))
    mb.box(0.95, 1.45, yr0, yr1 - 0.15, 0, 2.95, "stone_trim", skip=("bottom", "front", "top"))
    mb.box(-1.60, 1.60, yr0, yr1, 2.95, 3.55, dict(top="roof", default="travertine"), skip=("front",))
    mb.box(-0.95, 0.95, yr0, yr0 + 0.12, 0.15, 2.85, dict(back="vestibule", default="stone_trim"),
           skip=("front", "bottom", "top"))

    # Recessed front & right upper clerestory band (EZB..EZC above travertine EXLLU TOWER lintel, photo 155809)
    z_mid = (EZB + EZC) * 0.5
    for axis, c, s, a0, a1 in (("y", y_beam, -1, PORTICO_X0 + LP, PIER_X0),
                               ("x", PORTICO_X1, 1, EY + 1.90, 0.0)):
        K.paint(mb, axis, c, s, a0, a0 + 0.15, EZB + 0.06, EZC - 0.06, "travertine", layer=2)
        K.paint(mb, axis, c, s, a1 - 0.15, a1, EZB + 0.06, EZC - 0.06, "travertine", layer=2)
        K.paint(mb, axis, c, s, a0 + 0.15, a1 - 0.15, EZB + 0.06, EZC - 0.06, "clerestory", layer=2)
        for zb0, zb1 in ((EZB, EZB + 0.06), (z_mid - 0.025, z_mid + 0.025), (EZC - 0.06, EZC)):
            K.paint(mb, axis, c, s, a0, a1, zb0, zb1, "frame", layer=3)
        if axis == "y":
            for u in (0.25, 0.50, 0.75):
                mx = a0 + (a1 - a0) * u
                K.paint(mb, axis, c, s, mx - 0.03, mx + 0.03, EZB + 0.06, EZC - 0.06, "frame", layer=4)

    yl = EY + ST_N * ST_T
    zl = ST_N * ST_R
    # Solid stone cheek walls closing stair & pier gap
    mb.box(PORTICO_X0 + LP - 0.30, PORTICO_X0 + LP, EY + 1.15, 0.0, 0, zl + 0.15, "stone_trim",
           skip=("bottom", "front", "back"))
    mb.box(PIER_X0, PIER_X0 + 0.30, EY + 1.90, 0.0, 0, zl + 0.15, "stone_trim", skip=("bottom", "front", "back"))
    for i in range(ST_N):
        y0 = EY + i * ST_T
        mb.box(PORTICO_X0 + LP, PIER_X0, y0, y0 + ST_T, 0, ST_R * (i + 1), "canopy",
               skip=("bottom", "back", "left", "right"))
    # Main landing extending behind pink pier to meet accessible ramp at PORTICO_X1
    mb.box(PORTICO_X0 + LP, PIER_X0, yl, 0.0, 0, zl, "canopy", skip=("bottom", "back", "left", "right"))
    mb.box(PIER_X0 + 0.30, PORTICO_X1, yl, 0.0, 0, zl, "canopy", skip=("bottom", "back", "left"))
    # Recessed vestibule glazed facade + protruding stainless swing door surround + 3D revolving door
    mb.box(PORTICO_X0 + LP, PORTICO_X1, -0.06, 0.0, zl, EZ0, dict(front="vestibule", default="stone_trim"),
           skip=("bottom", "top", "back", "left", "right"))
    rev_cx, rev_r = -8.15, 1.08
    _revolving_door(mb, stage, rev_cx, -0.12, zl, zl + 2.66, r=rev_r)
    mb.box(-5.95, -4.15, -0.22, -0.06, zl, zl + 2.66, dict(front="vestibule", default="stainless"),
           skip=("bottom", "back"))
    if stage == 0:
        # Stainless swing-door mullions/push handles + continuous stainless transom bridging vestibule (photo 112)
        for sx0, sx1 in ((PORTICO_X0 + LP, rev_cx - rev_r - 0.05), (rev_cx + rev_r + 0.05, PORTICO_X1)):
            mb.box(sx0, sx1, -0.14, -0.06, zl + 2.66, EZ0, "stainless", skip=("back",))
        mb.box(-5.95, -4.15, -0.26, -0.22, zl + 2.58, zl + 2.68, "stainless", skip=("back",))
        mb.box(-5.08, -5.02, -0.25, -0.22, zl, zl + 2.58, "stainless", skip=("bottom", "top", "back"))
        for hx in (-5.20, -4.90):
            prism(mb, (hx, -0.29, zl + 0.75), (hx, -0.29, zl + 1.65), 0.036, "stainless")

    # Accessible ramp on right (+2.25 -> PORTICO_X1 = -1.70, behind pink pier, z = 0 -> zl)
    rx0, rx1, ry0, ry1 = PORTICO_X1, 2.25, -1.45, -0.35
    mb.quad([(rx1, ry0, 0.0), (rx1, ry1, 0.0), (rx0, ry1, zl), (rx0, ry0, zl)], A.uv("canopy"), "canopy")
    mb.tri([(rx0, ry0, 0.0), (rx1, ry0, 0.0), (rx0, ry0, zl)], A.uv("stone_trim")[:3], "stone_trim")
    mb.tri([(rx1, ry1, 0.0), (rx0, ry1, 0.0), (rx0, ry1, zl)], A.uv("stone_trim")[:3], "stone_trim")
    for tx in (rx0 + 0.05, -0.40, 0.90, rx1 - 0.15):
        tz = zl * (rx1 - tx) / (rx1 - rx0)
        prism(mb, (tx, ry0 + 0.06, tz), (tx, ry0 + 0.06, tz + 0.94), 0.068, "railing")
    for dz in (0.90, 0.50):
        prism(mb, (rx1 - 0.15, ry0 + 0.06, dz), (rx0 + 0.05, ry0 + 0.06, zl + dz), 0.042 if dz == 0.90 else 0.026,
              "railing")

    # Left raised stone planter + shrubs + 5-bar guardrail; right front planter + shrubs
    mb.box(-14.65, PORTICO_X0 - 0.06, -1.85, OUTER_Y0, 0, 0.92, "stone_trim", skip=("bottom", "back"))
    mb.box(-1.55, 2.35, -3.10, -1.60, 0, 0.72, "stone_trim", skip=("bottom",))
    if stage == 0:
        _shrubs(mb, -14.45, PORTICO_X0 - 0.30, -1.65, OUTER_Y0 - 0.20, 0.92, 0.58)
        _shrubs(mb, -1.35, 2.15, -2.90, -1.80, 0.72, 0.65)
        # 5-bar handrails + thicker stanchion posts (distinct half-widths prevent coplanar overlap)
        ya = EY + 0.20
        rail_z = lambda y: ST_R + (y - ya) / (yl - ya) * (zl - ST_R)
        for rx in (PORTICO_X0 + LP + 0.12, PIER_X0 - 0.10):
            for py, pz in ((ya, rail_z(ya)), ((ya + yl) / 2, rail_z((ya + yl) / 2)),
                           (yl, zl), (-0.25, zl)):
                prism(mb, (rx, py, pz), (rx, py, pz + 0.95), 0.068, "railing")
            for dz in (0.90, 0.72, 0.54, 0.36, 0.18):
                r = 0.044 if dz == 0.90 else 0.026
                y_end = yl - 0.035
                prism(mb, (rx, ya, dz + rail_z(ya)), (rx, y_end, dz + rail_z(y_end)), r, "railing")
                prism(mb, (rx, yl + 0.035, dz + zl), (rx, -0.09, dz + zl), r, "railing")
        # Left planter 5-bar safety railing + corner stanchions
        lp_x0, lp_x1, lp_y0 = -14.55, PORTICO_X0 - 0.18, -1.78
        for px, py in ((lp_x0, OUTER_Y0 - 0.08), (lp_x0, lp_y0), ((lp_x0 + lp_x1) / 2, lp_y0), (lp_x1, lp_y0)):
            prism(mb, (px, py, 0.92), (px, py, 1.87), 0.068, "railing")
        for dz in (0.90, 0.72, 0.54, 0.36, 0.18):
            r = 0.044 if dz == 0.90 else 0.026
            prism(mb, (lp_x0, OUTER_Y0 - 0.08, 0.92 + dz), (lp_x0, lp_y0 + 0.035, 0.92 + dz), r, "railing")
            prism(mb, (lp_x0 + 0.035, lp_y0, 0.92 + dz), (lp_x1, lp_y0, 0.92 + dz), r, "railing")
        # Pier inner wall sconces
        mb.box(PORTICO_X0 + LP, PORTICO_X0 + LP + 0.06, -2.90, -2.72, 2.35, 2.75,
               dict(right="ent_light", default="stone_trim"), skip=("left",))
        mb.box(PIER_X0 - 0.06, PIER_X0, -2.90, -2.72, 2.35, 2.75,
               dict(left="ent_light", default="stone_trim"), skip=("right",))


# ==============================================================================
# MAIN BUILDING ASSEMBLY
# ==============================================================================
def build(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    # Direct watertight CCW perimeter shell: 0..GH & GH..zf(PALE_F) dark granite (tiles align with floors), zf(PALE_F)..H upper cladding
    z_split = zf(PALE_F)
    for e in EDGES:
        (x0, y0), (x1, y1), tone = e["p0"], e["p1"], e["tone"]
        mb.rect([(x0, y0, 0.0), (x1, y1, 0.0), (x1, y1, GH), (x0, y0, GH)], "stone")
        mb.rect([(x0, y0, GH), (x1, y1, GH), (x1, y1, z_split), (x0, y0, z_split)], "stone")
        mb.rect([(x0, y0, z_split), (x1, y1, z_split), (x1, y1, H), (x0, y0, H)], tone)
    # Disjoint roof slab tiles at z = H (zero slice-to-slice seam lines)
    for x0, x1, y0, y1 in ROOF_RECTS:
        K.floor_quad(mb, x0, x1, y0, y1, H, "roof")

    ledges(mb, stage)
    roof(mb, stage)
    entrance(mb, stage)

    if stage == 0:
        facade_floor(mb, stage, 0, skip=(PORTICO_X0 - 0.25, PORTICO_X1 + 0.20))
        for f in range(1, NF):
            facade_floor(mb, stage, f)

    return mb


main = build(0)
lod1 = build(1)
lod2 = build(2)

K.export_asset(ASSET, 1, dict(main=main, lod1=lod1, lod2=lod2, windows=WS),
               A, K.out_dir_from_argv("output"), lot=(5, 4))
