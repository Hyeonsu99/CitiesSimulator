"""Tower 108: 50-floor Type C luxury tower on the OSM C-type outline, green-glass gabled crown,
round elevated helipad on the north wing, granite podium and portico.

Evidence:
  plan  OpenStreetMap way 934368145 (C outline shared by 105-108, 38.4 x 44.6 m, 1148 m2), overlaid on
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
    ctx.rgb[...] = np.array([80, 145, 138], np.float32)
    ctx.rgb += (ctx.v * 35.0)[..., None]
    fr = ((mx % 1.5) < 0.06) | (mz < 0.06) | (mz > ctx.tile[1] - 0.06) | ((mz % 2.0) < 0.06)
    ctx.rgb[fr] = np.array([230, 234, 232], np.float32)
    ctx.gloss[...] = np.where(fr, 0.4, 0.92)
    ctx.emis[...] = np.where(fr, 0.0, 0.05)


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
        ("deck_under", (62, 66, 70), 0.2, 0.35, 64),
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

PALE_F = 5                                    # granite podium below storey 5 (106 entrance photo), pale stone above
CELL = 5.2                                    # window bay pitch (large units; keeps main < 95k tris)
LEDGE_P, LEDGE_T = 0.55, 0.28                 # per-floor balcony ledge on the south / west faces (view_w_full.png)

# ------------------------------------------------------------------------------
# PLAN: OSM way 934368145 in (u = west, v = south) metres, orthogonalised to +-0.3 m.  x = u - 19.2, y = v.
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
# Window spans of the north walls next to the entrance, read from exllu-106/photos/auction_2022-112205_106_entrance.jpg
# (frontal, ~16 px/m): arm wall = 1-pane + 2-pane; main body wall = 4-pane + louvre + 2-pane.
ENT_SPANS = {
    ("y", 14.4, 10.6): ((13.0, 14.2, ()), (15.3, 18.1, HALF)),
    ("y", 15.4, -2.8): ((-0.3, 5.6, QUAD), (7.7, 10.3, HALF)),
}
ENT_LOUVRES = (("y", 15.4, -1, 5.8, 7.0),)


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
        for b0, b1, mull in ENT_SPANS.get((axis, c, a0)) or bays(a0, a1):
            if skip and axis == "y" and c == ENT_Y and s < 0 and b1 > skip[0] and b0 < skip[1]:
                continue
            window(mb, stage, axis, c, s, b0, b1, z0, z1, f, u, mull)
            u += 1
    if f > 0:
        for axis, c, s, a0, a1 in ENT_LOUVRES:
            louver(mb, stage, axis, c, s, a0, a1, z + 0.4, z1)


def ledges(mb):
    """Per-floor balcony ledges on the SW/south residential balcony wings (view_mid_hi, view_w_full, 108 photo)."""
    for axis, c, s, a0, a1, kind, _ in WALLS:
        if kind != "win" or s < 0 or a1 - a0 < 4.0:
            continue
        if not ((axis == "y" and c == 44.6) or (axis == "x" and a0 >= 26.8)):
            continue
        for f in range(1, NF):
            z = zf(f)
            mat = "grey_stone" if f < PALE_F else "pale"
            K.axbox(mb, axis, c, s, a0 + 0.1, a1 - 0.1, 0, LEDGE_P, z, z + LEDGE_T, mat,
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
        mb.rect([(ax, ay, H), (bx, by, H), (bx, by, PH), (ax, ay, PH)], "pale")
        mb.rect([(cx, cy, H), (dx, dy, H), (dx, dy, PH), (cx, cy, PH)], "pale")
        mb.quad([(ax, ay, PH), (bx, by, PH), (cx, cy, PH), (dx, dy, PH)], uv, "crown_white")


# Crown footprint on the main body (aerial: dark glazed frame between the helipad and the west arm)  # estimated
CX0, CX1, CY0, CY1 = -7.2, 7.6, 19.0, 33.0
CZ0, CZE, CZA = H + 0.6, H + 4.2, H + 9.5               # plinth top, eaves, apex


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
    mb.box(CX0, CX1, CY0, CY1, H, CZ0, "pale", skip=("bottom",))
    if stage == 2:
        # Lightweight closed gable massing for LOD2
        _gable_ear(mb, CX0, CX1, CY0, ym, CY1, CZ0, CZE, CZA, "crown_glass")
        return
    ew = 0.42
    _gable_ear(mb, CX0, CX0 + ew, CY0, ym, CY1, CZ0, CZE, CZA + 0.35, "crown_white")
    _gable_ear(mb, CX1 - ew, CX1, CY0, ym, CY1, CZ0, CZE, CZA + 0.35, "crown_white")
    # Solid glass slopes between the gable ears (closed underside soffit + eaves fascia)
    _sloped_slab(mb, CX0 + ew, CX1 - ew, CY0 - 0.1, CZE, ym, CZA, 0.22, "crown_glass", "soffit", "crown_white")
    _sloped_slab(mb, CX0 + ew, CX1 - ew, CY1 + 0.1, CZE, ym, CZA, 0.22, "crown_glass", "soffit", "crown_white")
    # North/south vertical glazed curtainwalls rising cleanly to the underside of the eaves (CZE - 0.22)
    mb.box(CX0 + ew, CX1 - ew, CY0 + 0.05, CY0 + 0.28, CZ0, CZE - 0.22, "crown_glass", skip=("bottom", "top"))
    mb.box(CX0 + ew, CX1 - ew, CY1 - 0.28, CY1 - 0.05, CZ0, CZE - 0.22, "crown_glass", skip=("bottom", "top"))
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
EZ0, EZB, EZC, EZT = 3.8, 4.65, 5.45, 5.85
PORTICO_X0, PORTICO_X1 = 10.6, 19.2           # 106 entrance photo: portico on the arm wall, pink pier at the outer corner
LP = 1.2
PIER_X0 = PORTICO_X1 - 1.95
ST_N, ST_R, ST_T = 7, 0.15, 0.36


def entrance(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    ZS = EZT - 0.2
    mb.box(PORTICO_X0, PORTICO_X1, EY, 0, EZ0, ZS, dict(front="pale", right="pale", left="pale", bottom="soffit"),
           skip=("back", "top"))
    mb.box(PORTICO_X0 - 0.1, PORTICO_X0 + LP, EY - 0.1, EY + 1.1, 0, ZS, "stone_trim", skip=("bottom", "top"))
    # Right corner pier: front wrap pink, rear/outer wrap dark granite (view_nw_base + 105 side photo)
    mb.box(PIER_X0, PORTICO_X1 + 0.2, EY - 0.2, EY + 0.65, 0, ZS,
           dict(front="pier_pink", right="pier_pink", left="stone_trim", default="pier_pink"),
           skip=("bottom", "top", "back"))
    mb.box(PIER_X0, PORTICO_X1 + 0.2, EY + 0.65, EY + 1.8, 0, ZS,
           dict(right="stone", left="stone_trim", back="stone", default="stone"),
           skip=("bottom", "top", "front"))
    mb.box(PORTICO_X0 - 0.2, PORTICO_X1 + 0.3, EY - 0.2, 0.0, ZS, EZT, dict(top="roof", default="stone_trim"),
           skip=("back",))
    if stage < 2:
        for axis, c, s, a0, a1 in (("y", EY, -1, PORTICO_X0 + LP, PIER_X0),
                                   ("x", PORTICO_X1, 1, EY + 1.8, 0.0),
                                   ("x", PORTICO_X0, -1, EY + 1.1, 0.0)):
            K.paint(mb, axis, c, s, a0, a1, EZC, ZS, "stone", layer=2)
            K.paint(mb, axis, c, s, a0 + 0.2, a1 - 0.2, EZB + 0.08, EZC - 0.08, "clerestory", layer=2)
            K.paint(mb, axis, c, s, a0, a1, EZB, EZB + 0.08, "frame", layer=3)
        yl = EY + ST_N * ST_T
        zl = ST_N * ST_R
        # Left stair cheek ends at yl so the behind-pillar bridge opens onto the main landing (ㄷ자 ramp entry)
        mb.box(PORTICO_X0 + LP - 0.3, PORTICO_X0 + LP, EY + 1.1, yl, 0, zl, "stone_trim",
               skip=("bottom", "front", "back"))
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
        # Revolving door housing + soffit-level trim forward of the glass doors (105/106/108 photos)
        cx_ent = (PORTICO_X0 + LP + PIER_X0) / 2 - 0.35
        mb.box(cx_ent - 0.95, cx_ent + 0.95, -0.45, -0.05, zl, zl + 2.45,
               dict(front="vestibule", left="vestibule", right="vestibule", top="stone_trim", default="stone_trim"),
               skip=("bottom", "back"))
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
def build(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    n = len(OUTLINE)
    for i in range(n):                         # outer walls straight from the outline
        (ax, ay), (bx, by) = OUTLINE[i], OUTLINE[(i + 1) % n]
        zp = zf(PALE_F)                        # two real faces instead of a paint decal: a decal 1 cm proud of the
        mb.rect([(ax, ay, 0.0), (bx, by, 0.0), (bx, by, zp), (ax, ay, zp)], "stone")    # wall overhangs convex
        mb.rect([(ax, ay, zp), (bx, by, zp), (bx, by, H), (ax, ay, H)], "pale")          # corners (LOD seam hole)
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

K.export_asset("HighriseTower108", 1, dict(main=main, lod1=lod1, lod2=lod2, windows=WS),
               A, K.out_dir_from_argv("output"), lot=(5, 6))
