"""Tower 104: 36-floor Type B tower, two staggered slabs joined by a core, flat segmented roof, modern portico.

Evidence: complex aerial (exllu-105/photos/dong_crops/grid.png: 101/104/109/112 show two offset slabs,
a central link with open light slots, stepped corners and NO helipad), entrance photos of 101/109/111/112.
Custom generator for Kumgang Exllu Tower 104 (27~28 py small/mid units, 36 floors, 108.1 m roof slab).
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

W, D, FH, NF = 29.7, 22.8, 2.94, 36          # 36 floors, 29.7 x 22.8 m footprint (OSM way 934368140) + 4 m portico
GH = 5.24                                     # double-height lobby storey
H = GH + FH * (NF - 1)                        # 108.14 m roof slab; core penthouse top ~111.6 m
REF_F = None                                  # 36-floor tower has standard residential floors throughout


def zf(f):
    """Floor level of storey f (0 = lobby)."""
    return 0.0 if f == 0 else GH + (f - 1) * FH


X = W / 2                                     # 14.85 m
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


def flat_emis(v):
    return lambda c: c.emis.__setitem__(Ellipsis, v)


TEX = {
    "stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 4, 0.3, 7.0, 0.12)),
    "maroon": dict(tile=(2.4, FH), px=512, painter=lambda c: granite(c, 2, 4, 0.18, 3.0)),
    "pale": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 3, 0.12, 2.5)),
    "grey_stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 4, 0.18, 4.0)),
    "window": dict(px=2048, painter=window_glass, emissive=(255, 205, 150)),
    "pier_pink": dict(tile=(1.2, 1.2), px=512, painter=lambda c: granite(c, 1, 2, 0.2, 9.0, 0.15)),
    "roof": dict(tile=(4.0, 4.0), px=512, painter=roofing),
    "canopy": dict(tile=(1.2, 1.2), px=256, painter=lambda c: paving(c, 2)),
    "louver": dict(tile=(0.6, 2.05), px=256, painter=shutter),
    "clerestory": dict(tile=(0.85, 0.64), px=128, painter=clerestory, emissive=(255, 232, 196)),
    "vestibule": dict(px=1024, painter=vestibule, emissive=(255, 226, 184)),
    "soffit": dict(tile=(1.2, 1.2), px=256, painter=soffit, emissive=(255, 226, 184)),
    "heli_net": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 4, 0.10, (178, 182, 184))),
    "heli_light": dict(px=32, painter=flat_emis(0.35), emissive=(110, 255, 140)),
    "heli_light_y": dict(px=32, painter=flat_emis(0.35), emissive=(255, 214, 90)),
    "obst_light": dict(px=32, painter=flat_emis(0.6), emissive=(255, 58, 40)),
}

A = K.Atlas(size=4096, pad=16)
for name, color, metal, gloss, px in (
        ("stone", (64, 70, 84), 0.0, 0.35, 128),           # photo 155809: blue-charcoal granite (#374762 zone)
        ("stone_trim", (60, 64, 76), 0.0, 0.35, 64),
        ("pale", (224, 222, 214), 0.0, 0.3, 128),
        ("maroon", (96, 48, 54), 0.0, 0.3, 128),
        ("crown_white", (232, 233, 230), 0.1, 0.4, 64),
        ("railing", (200, 203, 205), 0.6, 0.5, 64),
        ("frame", (236, 237, 235), 0.3, 0.5, 64),
        ("louver", (230, 231, 229), 0.2, 0.4, 64),
        ("roof", (120, 122, 122), 0.0, 0.3, 64),
        ("heli_green", (74, 140, 104), 0.0, 0.25, 64),
        ("heli_white", (232, 234, 226), 0.0, 0.25, 64),
        ("pier_pink", (176, 140, 130), 0.0, 0.4, 128),
        ("canopy", (160, 163, 162), 0.2, 0.45, 128),
        ("grey_stone", (168, 168, 164), 0.0, 0.3, 128),
        ("heli_net", (72, 76, 80), 0.6, 0.4, 64),
        ("heli_light", (90, 230, 120), 0.0, 0.6, 32),
        ("clerestory", (44, 58, 66), 0.5, 0.9, 128),
        ("vestibule", (46, 62, 66), 0.3, 0.9, 1024),
        ("soffit", (206, 208, 204), 0.0, 0.3, 256),
        ("heli_light_y", (240, 208, 96), 0.0, 0.6, 32),
        ("obst_light", (226, 62, 50), 0.0, 0.6, 32),
        ("brand_gold", (212, 175, 55), 0.8, 0.7, 64),
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
        zt = z0 + 0.55 * (z1 - z0)
        K.paint(mb, axis, c, s, a0, a1, zt, zt + 0.05, "frame", layer=lm + 1)


def louver(mb, stage, axis, c, s, a0, a1, z0, z1):
    if stage == 0:
        K.axbox(mb, axis, c, s, a0, a1, 0, 0.08, z0, z1, "louver")


WIDE = (0.1, 0.4, 0.46, 0.54, 0.6, 0.9)
PAIR = (0.18, 0.46, 0.54, 0.82)
QUAD = (0.22, 0.47, 0.53, 0.78)            # centre mullion pair: a single 0.5 bar trips the window-ray check
HALF = (0.47, 0.53)
CW = 0.15

PALE_F = 5                                    # dark granite podium below storey 5, pale stone above (photo 155809)

# ------------------------------------------------------------------------------
# PLAN from the OpenStreetMap footprint of the B-type towers (ways 934368139/40/37/38 = 101/104/109/112,
# one identical 24-vertex outline, 29.7 x 22.8 m, 531 m2).  The wide edge with a 3 m x 4.6 m central
# notch is the entrance face (photos 155129/155809: full-height dark recess between two pale wings).
# Behind the front block the sides step in and out (outline vertices, symmetrised to +-0.2 m).
# ------------------------------------------------------------------------------
RW, RD = 1.5, 4.5                             # front recess half width / depth
NX = 5.35                                     # outer front bays (dark left / maroon right) -- photo 155809
SLICES = ((0.0, 7.0, X), (7.0, 10.9, 11.6), (10.9, 13.6, 9.4), (13.6, 17.4, 11.8), (17.4, D, 10.2))  # (y0, y1, half width)


def _plan():
    mass, steps, walls = [], [], []
    for i, (y0, y1, hw) in enumerate(SLICES):
        sk = ["bottom"] + (["front"] if i else []) + (["back"] if i < len(SLICES) - 1 else [])
        if i == 0:                            # front block split by the recess
            mass += [(-hw, -RW, 0.0, RD, ("bottom", "back")), (RW, hw, 0.0, RD, ("bottom", "back")),
                     (-hw, hw, RD, y1, ("bottom", "front", "back"))]
            steps.append(("y", RD, -1, -RW, RW))                      # recess back wall
            walls += [("x", -RW, 1, 0.0, RD, "slot", "dark"), ("x", RW, -1, 0.0, RD, "slot", "dark"),
                      ("y", RD, -1, -RW, RW, "win", "dark")]
        else:
            mass.append((-hw, hw, y0, y1, tuple(sk)))
        walls += [("x", -hw, -1, y0, y1, "win", "pale"), ("x", hw, 1, y0, y1, "win", "pale")]
        if i < len(SLICES) - 1:               # exposed strips where the next slice is narrower / wider
            nhw = SLICES[i + 1][2]
            s_ = 1 if nhw < hw else -1        # facing back (+Y) when stepping in
            for a0, a1 in ((-max(hw, nhw), -min(hw, nhw)), (min(hw, nhw), max(hw, nhw))):
                steps.append(("y", y1, s_, a0, a1))
                walls.append(("y", y1, s_, a0, a1, "win" if a1 - a0 > 2.6 else "wall", "dark"))
    hw = SLICES[-1][2]
    walls.append(("y", D, 1, -hw, hw, "win", "pale"))
    return mass, steps, walls


MASS, STEPS, _walls = _plan()
WALLS = (
    ("y", 0.0, -1, -X, -X + NX, "win", "dark"),
    ("y", 0.0, -1, -X + NX, -RW, "win", "pale"),
    ("y", 0.0, -1, RW, X - NX, "win", "pale"),
    ("y", 0.0, -1, X - NX, X, "win", "maroon"),         # photo 155129: right outer bay is maroon above the podium
) + tuple(_walls)
# Front-face window spans read from photo 155809 (frontal, ~40.8 px/m from the 2.94 m floor pitch):
# wing = one 4-pane 5.15 m window 1.2 m from the recess; outer bay = 2-pane 2.45 m + 1-pane 1.1 m.
FRONT_SPANS = {
    ("y", 0.0, -X + NX): ((-RW - 6.35, -RW - 1.2, QUAD),),
    ("y", 0.0, RW): ((RW + 1.2, RW + 6.35, QUAD),),            # photo_check warp: u 0.15..0.80 of the wing
    ("y", 0.0, -X): ((-X + 1.35, -X + 3.8, HALF), (-X + 4.1, -X + NX - 0.25, ())),
    ("y", 0.0, X - NX): ((X - NX + 0.25, X - 4.1, ()), (X - 3.8, X - 1.35, HALF)),
}
CELL = 3.7                                    # window bay pitch along a wall


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
    """All windows and slot louvers of storey f; skip=(a0, a1) leaves the front span free for the portico."""
    z = zf(f)
    z0, z1 = (0.4, GH - 0.6) if f == 0 else (z + SILL, z + HEAD)
    u = 0
    for axis, c, s, a0, a1, kind, _ in WALLS:
        if kind == "slot":
            if f > 0:
                for b0, b1, _ in bays(a0, a1):
                    louver(mb, stage, axis, c, s, b0 + 0.4, b1 - 0.4, z + 0.4, z1)
            continue
        if kind != "win":
            continue
        for b0, b1, mull in FRONT_SPANS.get((axis, c, a0)) or bays(a0, a1):
            if skip and axis == "y" and c == 0.0 and b1 > skip[0] and b0 < skip[1]:
                continue
            window(mb, stage, axis, c, s, b0, b1, z0, z1, f, u, mull); u += 1


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
# FLAT SEGMENTED ROOF: parapets on every slab edge, core stair/lift penthouse, small plant boxes.
# Aerial shows no helipad marking on any B-type tower.
# ==============================================================================
PT = 0.35                                     # parapet thickness
PH = H + 1.4                                  # parapet top


def outline():
    """Roof outline, counter-clockwise seen from above: front with the recess, right steps, back, left steps."""
    pts = [(-X, 0.0), (-RW, 0.0), (-RW, RD), (RW, RD), (RW, 0.0)]
    for i, (_, y1, hw) in enumerate(SLICES):
        pts.append((hw, SLICES[i - 1][1] if i else 0.0))
        pts.append((hw, y1))
    for i, (y0, _, hw) in reversed(list(enumerate(SLICES))):
        pts.append((-hw, SLICES[i][1]))
        pts.append((-hw, y0))
    out = []                                  # drop repeated / collinear points
    for p in pts:
        if not out or p != out[-1]:
            out.append(p)
    if out[0] == out[-1]:
        out.pop()
    keep = []
    n = len(out)
    for i, p in enumerate(out):
        a, b = out[i - 1], out[(i + 1) % n]
        if (p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0]) != 0:
            keep.append(p)
    return keep


def parapet_ring(mb):
    """One continuous mitred parapet: inset every outline vertex by PT along both adjacent inward normals."""
    P = outline()
    n = len(P)

    def inward(a, b):                         # left normal of edge a->b (inside for a CCW outline)
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
        mb.rect([(ax, ay, H), (bx, by, H), (bx, by, PH), (ax, ay, PH)], "pale")      # outer face
        mb.rect([(cx, cy, H), (dx, dy, H), (dx, dy, PH), (cx, cy, PH)], "pale")      # inner face
        mb.quad([(ax, ay, PH), (bx, by, PH), (cx, cy, PH), (dx, dy, PH)], uv, "crown_white")  # coping


def roof(mb, stage):
    parapet_ring(mb)
    # Core penthouse (stairs / lift overrun) and plant boxes on each slab
    mb.box(-4.0, 4.0, 8.0, 15.0, H, H + 3.5, dict(top="roof", default="crown_white"), skip=("bottom",))
    if stage < 2:
        for x0, x1, y0, y1 in ((-11.0, -7.0, 1.5, 5.0), (5.5, 9.5, 18.0, 21.5)):
            mb.box(x0, x1, y0, y1, H, H + 1.8, dict(top="roof", default="crown_white"), skip=("bottom",))
    if stage == 0:
        bw = SLICES[-1][2]
        for xc, yc in ((-X + 0.2, 0.2), (X - 0.2, 0.2), (-bw + 0.2, D - 0.2), (bw - 0.2, D - 0.2)):
            mb.box(xc - 0.12, xc + 0.12, yc - 0.12, yc + 0.12, PH, PH + 0.25, "obst_light", skip=("bottom",))
        mb.box(-0.15, 0.15, 11.35, 11.65, H + 3.5, H + 3.8, "obst_light", skip=("bottom",))


# ==============================================================================
# ENTRANCE PORCH
# ==============================================================================
EY = -3.95
EZ0, EZB, EZC, EZT = 3.8, 4.65, 5.45, 5.85
PORTICO_X0, PORTICO_X1 = -X + NX - 2.0, -RW - 0.2  # wide dark left pier over the set-back, pink pier at the recess edge
LP = 2.0                                      # left pier width (photo 155809)
PIER_X0 = PORTICO_X1 - 1.95                   # pink pier inner face
ST_N, ST_R, ST_T = 7, 0.15, 0.36


def entrance(mb, stage):
    ZS = EZT - 0.2
    # Canopy ceiling & fascia
    mb.box(PORTICO_X0, PORTICO_X1, EY, 0, EZ0, ZS, dict(front="pale", right="pale", left="pale", bottom="soffit"),
           skip=("back", "top"))
    # Left dark granite pier
    mb.box(PORTICO_X0 - 0.1, PORTICO_X0 + LP, EY - 0.1, EY + 1.1, 0, ZS, "stone_trim", skip=("bottom", "top"))
    # Right massive pink granite pier (dong numeral not modelled)
    mb.box(PIER_X0, PORTICO_X1 + 0.2, EY - 0.2, EY + 1.8, 0, ZS,
           dict(front="pier_pink", right="pier_pink", left="stone_trim", default="pier_pink"),
           skip=("bottom", "top"))
    # Dark roof slab over porch
    mb.box(PORTICO_X0 - 0.2, PORTICO_X1 + 0.3, EY - 0.2, 0.0, ZS, EZT, dict(top="roof", default="stone_trim"))

    if stage < 2:
        for axis, c, s, a0, a1 in (("y", EY, -1, PORTICO_X0 + LP, PIER_X0),
                                   ("x", PORTICO_X1, 1, EY + 1.8, 0.0),
                                   ("x", PORTICO_X0, -1, EY + 1.1, 0.0)):
            K.paint(mb, axis, c, s, a0, a1, EZC, ZS, "stone", layer=2)
            K.paint(mb, axis, c, s, a0 + 0.2, a1 - 0.2, EZB + 0.08, EZC - 0.08, "clerestory", layer=2)
            K.paint(mb, axis, c, s, a0, a1, EZB, EZB + 0.08, "frame", layer=3)

        yl = EY + ST_N * ST_T
        zl = ST_N * ST_R
        # Solid stone cheek walls close the stair sides between the piers and the facade
        mb.box(PORTICO_X0 + LP - 0.3, PORTICO_X0 + LP, EY + 1.1, 0.0, 0, zl + 0.15, "stone_trim",
               skip=("bottom", "front", "back"))
        mb.box(PIER_X0, PIER_X0 + 0.3, EY + 1.8, 0.0, 0, zl + 0.15, "stone_trim", skip=("bottom", "front", "back"))
        for i in range(ST_N):
            y0 = EY + i * ST_T
            mb.box(PORTICO_X0 + LP, PIER_X0, y0, y0 + ST_T, 0, ST_R * (i + 1), "canopy",
                   skip=("bottom", "back", "left", "right"))
        zl = ST_N * ST_R
        mb.box(PORTICO_X0 + LP, PIER_X0, yl, 0, 0, zl, "canopy", skip=("bottom", "back", "left", "right"))
        mb.box(PORTICO_X0 + LP, PIER_X0, -0.05, 0.0, zl, EZ0, {"front": "vestibule", "default": "stone_trim"},
               skip=("bottom", "top", "back", "left", "right"))

        # Safety railings (5 bars)
        ya = EY + 0.2
        rail_z = lambda y: ST_R + (y - ya) / (yl - ya) * (zl - ST_R)
        xl = PORTICO_X0 + LP + 0.1
        for dz in (0.9, 0.45):
            prism(mb, (xl, ya, dz + rail_z(ya)), (xl, yl, dz + rail_z(yl)), 0.05, "railing")
            prism(mb, (xl, yl, dz + zl), (xl, -0.05, dz + zl), 0.05, "railing")
        xr = PIER_X0 - 0.05
        for dz in (0.90, 0.72, 0.54, 0.36, 0.18):
            prism(mb, (xr, ya, dz + rail_z(ya)), (xr, yl, dz + rail_z(yl)), 0.04 if dz < 0.9 else 0.05, "railing")
            prism(mb, (xr, yl, dz + zl), (xr, 0.0, dz + zl), 0.04 if dz < 0.9 else 0.05, "railing")


# ==============================================================================
# MAIN BUILDING ASSEMBLY
# ==============================================================================
def build(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    for x0, x1, y0, y1, sk in MASS:
        mb.box(x0, x1, y0, y1, 0, H, dict(top="roof", default="stone"), skip=sk)
    for _, y, s_, a0, a1 in STEPS:            # exposed strips where adjacent slices differ in width
        q = [(a0, y, 0.0), (a1, y, 0.0), (a1, y, H), (a0, y, H)] if s_ < 0 else             [(a1, y, 0.0), (a0, y, 0.0), (a0, y, H), (a1, y, H)]
        mb.rect(q, "stone")

    # Pale stone above the dark granite podium on every exposed wall
    for axis, c, s, a0, a1, _, tone in WALLS:
        if tone != "dark":
            K.paint(mb, axis, c, s, a0, a1, zf(PALE_F), H, tone)

    roof(mb, stage)

    # Entrance Porch & Terrace
    entrance(mb, stage)

    # Windows
    if stage == 0:
        facade_floor(mb, stage, 0, skip=(PORTICO_X0 - 0.5, PORTICO_X1 + 0.5))
        for f in range(1, NF):
            facade_floor(mb, stage, f)

    return mb


main = build(0)
lod1 = build(1)
lod2 = build(2)

K.export_asset("HighriseTower104", 1, dict(main=main, lod1=lod1, lod2=lod2, windows=WS),
               A, K.out_dir_from_argv("output"), lot=(5, 4))
