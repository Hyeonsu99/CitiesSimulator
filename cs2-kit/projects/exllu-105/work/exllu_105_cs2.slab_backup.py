"""Tower 105: 50-floor luxury slab tower with green-glazed sloped roof conservatory crown,
rooftop helipad, per-floor projecting balcony ledges on the west face, and distinctive entrance portico.

Evidence: photos/view_n_hi.png, view_nw_base.png, view_top_far_w.png, sat.png.
Custom generator for Kumgang Exllu Tower 105 (42, 48, 58 py large units).
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

# No separate _Gls glass mesh: avoids night z-fighting flicker verified in tower 103 tests.

W, D, FH, NF = 34.0, 21.4, 2.94, 50          # 50 floors, 2.94 m floor height, 34 x 21.4 m footprint (5x4 lot)
GH = 5.24                                     # double-height lobby storey
H = GH + FH * (NF - 1)                        # 149.3 m roof slab; crown top reaches 160.0 m
REF_F = 26                                    # refuge floor (window-less louver band at mid height)


def zf(f):
    """Floor level of storey f (0 = lobby)."""
    return 0.0 if f == 0 else GH + (f - 1) * FH


X = W / 2                                     # 17.0 m
RX, RD = 1.0, 1.8                             # front subtle recess slot
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


VEST_W, VEST_H = 5.4, 2.75


def vestibule(ctx):
    x, z = ctx.u * VEST_W, ctx.v * VEST_H
    ctx.rgb[...] = np.array([46, 62, 66], np.float32)
    ctx.rgb += (ctx.v * 34.0)[..., None]
    ctx.rgb += (((x * 0.6 + z) % 1.7 < 0.10) * 16.0)[..., None]
    ctx.gloss[...] = 0.9
    ctx.emis[...] = 0.07 + 0.03 * (z < 2.1)
    steel = np.array([172, 176, 178], np.float32)
    fr = (x < 0.07) | (x > VEST_W - 0.07) | (z < 0.06) | (z > VEST_H - 0.07) | (np.abs(z - 2.15) < 0.035)
    for xm in (1.1, VEST_W - 1.1):
        fr |= np.abs(x - xm) < 0.035
    door = (x > 1.1) & (x < VEST_W - 1.1) & (z < 2.15)
    fr |= door & ((np.abs(x - VEST_W / 2) < 0.03) | (np.abs(x - 1.9) < 0.025) | (np.abs(x - (VEST_W - 1.9)) < 0.025))
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
    # Lit rooms rule: contiguous 7 cells of 25 with 16 px guard band (anti-dot flicker)
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


def deck_glow(ctx):
    mx, mz = ctx.meters()
    d = np.hypot(mx - ctx.tile[0] / 2, mz - ctx.tile[1] / 2)
    ctx.rgb[d < 0.17] = np.array([96, 100, 100], np.float32)


def flat_emis(v):
    return lambda c: c.emis.__setitem__(Ellipsis, v)


DECK_W = 0.85
CROWN_GH = 4.5


def crown_sloped_glass(ctx):
    """Green glazed sloped crown glass (photos/view_top_far_w.png, sat.png, site.jpg):
    distinctive triangular/trapezoidal conservatory crown roof with white structural mullions."""
    mx, mz = ctx.meters()
    ctx.rgb[...] = np.array([80, 145, 138], np.float32)
    ctx.rgb += (ctx.v * 35.0)[..., None]
    # Structural mullions every 1.5 m along x and horizontal transom
    fr = ((mx % 1.5) < 0.06) | (mx < 0.06) | (mx > ctx.tile[0] - 0.06) | (mz < 0.06) | (mz > ctx.tile[1] - 0.06) | ((mz % 2.0) < 0.06)
    ctx.rgb[fr] = np.array([230, 234, 232], np.float32)
    ctx.gloss[...] = np.where(fr, 0.4, 0.92)
    ctx.emis[...] = np.where(fr, 0.0, 0.05)


TEX = {
    "stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 4, 0.3, 7.0, 0.12)),
    "pale": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 3, 0.12, 2.5)),
    "grey_stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 4, 0.18, 4.0)),
    "window": dict(px=2048, painter=window_glass, emissive=(255, 205, 150)),
    "pier_pink": dict(tile=(1.2, 1.2), px=512, painter=lambda c: granite(c, 1, 2, 0.2, 9.0, 0.15)),
    "crown_glass": dict(tile=(3.0, 4.0), px=512, painter=crown_sloped_glass, emissive=(210, 255, 230)),
    "roof": dict(tile=(4.0, 4.0), px=512, painter=roofing),
    "canopy": dict(tile=(1.2, 1.2), px=256, painter=lambda c: paving(c, 2)),
    "white_shaft": dict(tile=(2.4, FH), px=256, painter=lambda c: paving(c, 2)),
    "louver": dict(tile=(0.6, 2.05), px=256, painter=shutter),
    "clerestory": dict(tile=(0.85, 0.64), px=128, painter=clerestory, emissive=(255, 232, 196)),
    "vestibule": dict(px=1024, painter=vestibule, emissive=(255, 226, 184)),
    "soffit": dict(tile=(1.2, 1.2), px=256, painter=soffit, emissive=(255, 226, 184)),
    "ent_light": dict(px=32, painter=lambda c: c.emis.__setitem__(Ellipsis, 0.25), emissive=(255, 226, 184)),
    "heli_net": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 4, 0.10, (178, 182, 184))),
    "grating": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 12, 0.25, (70, 72, 74))),
    "heli_light": dict(px=32, painter=flat_emis(0.35), emissive=(110, 255, 140)),
    "deck_lit": dict(tile=((2 * 5.2 - DECK_W) / 7, DECK_W), px=128, painter=deck_glow),
    "heli_light_y": dict(px=32, painter=flat_emis(0.35), emissive=(255, 214, 90)),
    "obst_light": dict(px=32, painter=flat_emis(0.6), emissive=(255, 58, 40)),
    "under_light": dict(px=32, painter=lambda c: c.emis.__setitem__(Ellipsis, 0.15), emissive=(255, 214, 160)),
}

A = K.Atlas(size=4096, pad=16)

for name, color, metal, gloss, px in (
        ("stone", (88, 82, 80), 0.0, 0.35, 128),
        ("stone_trim", (84, 78, 77), 0.0, 0.35, 64),
        ("pale", (224, 222, 214), 0.0, 0.3, 128),
        ("crown_white", (232, 233, 230), 0.1, 0.4, 64),
        ("deck_under", (62, 66, 70), 0.2, 0.35, 64),
        ("crown_glass", (100, 165, 155), 0.4, 0.9, 128),
        ("railing", (200, 203, 205), 0.6, 0.5, 64),
        ("frame", (236, 237, 235), 0.3, 0.5, 64),
        ("louver", (230, 231, 229), 0.2, 0.4, 64),
        ("louver_back", (58, 60, 62), 0.0, 0.3, 64),
        ("roof", (120, 122, 122), 0.0, 0.3, 64),
        ("deck", (150, 152, 150), 0.0, 0.3, 64),
        ("heli_green", (74, 140, 104), 0.0, 0.25, 64),
        ("heli_white", (232, 234, 226), 0.0, 0.25, 64),
        ("pier_pink", (176, 140, 130), 0.0, 0.4, 128),
        ("canopy", (160, 163, 162), 0.2, 0.45, 128),
        ("grey_stone", (168, 168, 164), 0.0, 0.3, 128),
        ("pale_trim", (226, 224, 218), 0.0, 0.3, 64),
        ("grey_trim", (150, 151, 148), 0.0, 0.3, 64),
        ("heli_net", (72, 76, 80), 0.6, 0.4, 64),
        ("grating", (128, 132, 134), 0.6, 0.35, 64),
        ("heli_light", (90, 230, 120), 0.0, 0.6, 32),
        ("clerestory", (44, 58, 66), 0.5, 0.9, 128),
        ("vestibule", (46, 62, 66), 0.3, 0.9, 1024),
        ("soffit", (206, 208, 204), 0.0, 0.3, 256),
        ("ent_light", (250, 240, 220), 0.0, 0.6, 32),
        ("deck_lit", (150, 152, 150), 0.0, 0.3, 128),
        ("heli_light_y", (240, 208, 96), 0.0, 0.6, 32),
        ("obst_light", (226, 62, 50), 0.0, 0.6, 32),
        ("flood_light", (246, 244, 234), 0.0, 0.6, 32),
        ("windsock", (236, 112, 44), 0.0, 0.2, 32),
        ("under_light", (250, 236, 210), 0.0, 0.6, 32),
        ("brand_gold", (185, 155, 95), 0.3, 0.5, 64),
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


WIDE3 = (0.28, 0.34, 0.62, 0.68)           # 3-pane wide living room window
PAIR = (0.2, 0.46, 0.54, 0.8)
SLIT = ()                                  # single slit window
CW = 0.15                                  # corner post gap
PALE_F_LEFT = 6                            # base granite to floor 6 on left wing
PALE_F_RIGHT = 8                           # base granite extends to floor 8 on right wing (view_n_hi.png)

# 105 facade window ranges (34 m width: x from -17 to 17)
# Left wing (-x): Corner window (-16.85..-13.8), Wide living room (-12.8..-8.8), AC Louver (-8.5..-7.4), Mid window (-6.2..-3.2)
# Center recess (-RX..RX = -1.0..1.0): Slot window (-0.6..0.6)
# Right wing (+x): Mid window (3.2..6.2), Slit window (7.6..8.6), Bedroom window (9.8..13.2), Corner window (14.2..16.85)

# West side (+x = 17.0): stepped projecting balcony ledges every floor
WEST_LEDGE_Y0, WEST_LEDGE_Y1 = 4.0, 18.0

# Back side (D = 22.0)
BACK_WINS = ((-15.5, -12.0, PAIR), (-10.5, -6.5, WIDE3), (-5.0, -1.8, PAIR),
             (2.0, 6.0, PAIR), (8.0, 12.0, WIDE3), (13.5, 15.5, (0.38,)))


def ring(mb, cx, cy, r0, z0, r1, z1, region, n, flip=False, rot=0.0):
    """Band of n quads between polygon (r0, z0) and polygon (r1, z1)."""
    for i in range(n):
        a, b = rot + 2 * math.pi * i / n, rot + 2 * math.pi * (i + 1) / n
        q = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0), (cx + r0 * math.cos(b), cy + r0 * math.sin(b), z0),
             (cx + r1 * math.cos(b), cy + r1 * math.sin(b), z1), (cx + r1 * math.cos(a), cy + r1 * math.sin(a), z1)]
        mb.rect(q[::-1] if flip else q, region)


def prism(mb, p0, p1, w, region):
    d = [b - a for a, b in zip(p0, p1)]
    L = math.sqrt(sum(v * v for v in d))
    t = [v / L for v in d]
    u = [t[1], -t[0], 0.0]
    n = math.hypot(u[0], u[1]) or 1.0
    u = [v / n * w / 2 for v in u]
    v = [t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0]]
    vn = math.sqrt(sum(k * k for k in v)) or 1.0
    v = [k / vn * w / 2 for k in v]
    corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    for i in range(4):
        (a1, b1), (a2, b2) = corners[i], corners[(i + 1) % 4]
        off1 = [a1 * u[k] + b1 * v[k] for k in range(3)]
        off2 = [a2 * u[k] + b2 * v[k] for k in range(3)]
        q = [tuple(p0[k] + off1[k] for k in range(3)), tuple(p0[k] + off2[k] for k in range(3)),
             tuple(p1[k] + off2[k] for k in range(3)), tuple(p1[k] + off1[k] for k in range(3))]
        mb.rect(q, region)


def floor_facade(mb, stage, f):
    z = zf(f)
    z0, z1, u = z + SILL, z + HEAD, 0

    # North (front) facade (view_n_hi.png)
    # Left wing
    window(mb, stage, "y", 0, -1, -(X - CW), -13.8, z0, z1, f, u, PAIR, jambs=(False, True)); u += 1
    window(mb, stage, "y", 0, -1, -12.8, -8.8, z0, z1, f, u, WIDE3); u += 1
    louver(mb, stage, "y", 0, -1, -8.5, -7.4, z + 0.35, z1)
    window(mb, stage, "y", 0, -1, -6.4, -3.4, z0, z1, f, u, PAIR); u += 1

    # Recess slot
    window(mb, stage, "y", RD, -1, -0.6, 0.6, z0, z1, f, u, (0.38,)); u += 1

    # Right wing
    window(mb, stage, "y", 0, -1, 3.4, 6.4, z0, z1, f, u, PAIR); u += 1
    window(mb, stage, "y", 0, -1, 7.6, 8.6, z0, z1, f, u, SLIT); u += 1
    window(mb, stage, "y", 0, -1, 9.8, 13.8, z0, z1, f, u, WIDE3); u += 1
    window(mb, stage, "y", 0, -1, 14.6, X - CW, z0, z1, f, u, PAIR, jambs=(True, False)); u += 1

    # West side (+x = X)
    window(mb, stage, "x", X, 1, 1.0, 4.0, z0, z1, f, u, PAIR); u += 1
    window(mb, stage, "x", X, 1, 6.0, 10.0, z0, z1, f, u, WIDE3); u += 1
    window(mb, stage, "x", X, 1, 12.0, 16.0, z0, z1, f, u, WIDE3); u += 1
    window(mb, stage, "x", X, 1, 17.5, 20.5, z0, z1, f, u, PAIR); u += 1

    # East side (-x = -X)
    window(mb, stage, "x", -X, -1, 1.5, 5.0, z0, z1, f, u, PAIR); u += 1
    window(mb, stage, "x", -X, -1, 7.0, 11.0, z0, z1, f, u, WIDE3); u += 1
    louver(mb, stage, "x", -X, -1, 12.0, 13.2, z + 0.35, z1)
    window(mb, stage, "x", -X, -1, 14.5, 18.5, z0, z1, f, u, PAIR); u += 1

    # Back side (D)
    for a0, a1, m in BACK_WINS:
        window(mb, stage, "y", D, 1, a0, a1, z0, z1, f, u, m); u += 1


def ground_floor(mb, stage):
    z0, z1, u = 0.4, GH - 0.7, 0
    # Lobby glazing (avoid entrance pier at x 14.2..16.2)
    window(mb, stage, "y", 0, -1, 16.25, 16.85, z0, z1, 0, u); u += 1
    window(mb, stage, "y", 0, -1, -15.5, -13.0, z0, z1, 0, u); u += 1
    window(mb, stage, "x", X, 1, 1.2, 5.5, z0, z1, 0, u, PAIR); u += 1
    window(mb, stage, "x", -X, -1, 1.2, 5.5, z0, z1, 0, u, PAIR); u += 1
    for a0, a1, m in BACK_WINS:
        window(mb, stage, "y", D, 1, a0, a1, z0, z1, 0, u, m); u += 1


# ==============================================================================
# ROOF & CONSERVATORY CROWN & HELIPAD
# ==============================================================================
# Green glazed sloped conservatory crown on the north/center ridge + detailed rooftop helipad
# Total height matches 160.0 m max height.
CROWN_X0, CROWN_X1 = -14.5, 0.8
CROWN_Y0, CROWN_Y1 = 4.5, 16.9
CROWN_Z0 = H + 0.6
CROWN_Z_APEX = H + 9.5
CROWN_Z_EAVES = H + 4.2

# Helipad on the eastern roof area (+x)
HX, HY = 10.0, 10.7
HS = 5.2
HCORE = 1.3
HZ0 = H + 5.5
HZ1 = H + 7.4
HZT = H + 8.0
SQ = math.pi / 4
RC = HS * math.sqrt(2)
NET = 1.0
PX0 = HX - HS - NET


def under_z(d):
    """Height of the sloped square underside at Chebyshev distance d from the deck centre."""
    return HZ0 + (HZ1 - HZ0) * (d - 1.41) / (HS - 1.41)


def heli_underside(mb, stage):
    """Underside structure: collar node on core, 8 struts to underside, 8 radial ribs, 8 warm downlights."""
    zc0, zc1 = H + 2.5, H + 3.1
    n = 32 if stage == 0 else 16
    ring(mb, HX, HY, HCORE + 0.18, zc0, HCORE + 0.18, zc1, "crown_white", n)
    ring(mb, HX, HY, HCORE + 0.18, zc1, HCORE, zc1, "crown_white", n)
    ring(mb, HX, HY, HCORE + 0.18, zc0, HCORE, zc0, "crown_white", n, flip=True)
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        c, s = math.cos(a), math.sin(a)
        k = max(abs(c), abs(s))
        d1 = 0.78 * HS
        prism(mb, (HX + (HCORE + 0.1) * c, HY + (HCORE + 0.1) * s, (zc0 + zc1) / 2),
              (HX + d1 / k * c, HY + d1 / k * s, under_z(d1) + 0.15), 0.35, "crown_white")
    if stage > 0:
        return
    for i in range(8):
        a = 2 * math.pi * i / 8
        c, s = math.cos(a), math.sin(a)
        k = max(abs(c), abs(s))
        d0, d1 = 1.6, HS - 0.15
        prism(mb, (HX + d0 / k * c, HY + d0 / k * s, under_z(d0) - 0.18),
              (HX + d1 / k * c, HY + d1 / k * s, under_z(d1) - 0.18), 0.18, "crown_white")
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        c, s = math.cos(a), math.sin(a)
        d = 3.6
        x, y = HX + d / max(abs(c), abs(s)) * c, HY + d / max(abs(c), abs(s)) * s
        z = under_z(d)
        mb.box(x - 0.25, x + 0.25, y - 0.25, y + 0.25, z - 0.15, z - 0.04, "under_light", skip=("top",))


def heli_net(mb):
    """Perimeter safety net on North, East and South edges; steel grating access platform on West edge."""
    z0, z1 = HZT - 0.19, HZT - 0.02
    xe, y0, y1 = HX + HS, HY - HS, HY + HS
    mb.box(xe, xe + NET, y0 - NET, y1 + NET, z0, z1, "heli_net", skip=("left",))
    mb.box(PX0, xe, y1, y1 + NET, z0, z1, "heli_net", skip=("front", "right"))
    mb.box(PX0, xe, y0 - NET, y0, z0, z1, "heli_net", skip=("back", "right"))
    mb.box(PX0, HX - HS, y0, y1, z0, z1, "grating", skip=("right", "front", "back"))


def heli_lights(mb, stage):
    """Helideck night lighting: green perimeter lights with light pools on deck band,
    yellow touchdown-circle lights, rail-top floodlights facing pad, red obstruction lights, and lit windsock."""
    w, z = DECK_W, HZT + 0.03
    L = 2 * HS - w
    T = L / 7
    x0, x1, y0, y1 = HX - HS, HX + HS, HY - HS, HY + HS
    strips = (((x0, y0), (1, 0), (0, 1)), ((x1, y0), (0, 1), (-1, 0)),
              ((x1, y1), (-1, 0), (0, -1)), ((x0, y1), (0, -1), (1, 0)))
    for (ox, oy), (ax, ay), (cx, cy) in strips:
        mb.rect([(ox, oy, z), (ox + ax * L, oy + ay * L, z),
                 (ox + ax * L + cx * w, oy + ay * L + cy * w, z), (ox + cx * w, oy + cy * w, z)], "deck_lit")
        if stage == 0:
            for i in range(7):
                x = ox + ax * (i + 0.5) * T + cx * w / 2
                y = oy + ay * (i + 0.5) * T + cy * w / 2
                mb.box(x - 0.08, x + 0.08, y - 0.08, y + 0.08, z, z + 0.08, "heli_light", skip=("bottom",))
    if stage > 0:
        return
    for i in range(16):
        a = 2 * math.pi * (i + 0.5) / 16
        x, y = HX + 2.64 * math.cos(a), HY + 2.64 * math.sin(a)
        mb.box(x - 0.06, x + 0.06, y - 0.06, y + 0.06, HZT + 0.06, HZT + 0.12, "heli_light_y", skip=("bottom",))
    zr = HZT + 0.9
    body = dict(default="railing", top="railing")
    for t in (-2.5, 2.5):
        mb.box(HX + t - 0.25, HX + t + 0.25, y0 - 0.12, y0 + 0.05, zr, zr + 0.18, dict(body, back="flood_light"), skip=("bottom",))
        mb.box(HX + t - 0.25, HX + t + 0.25, y1 - 0.05, y1 + 0.12, zr, zr + 0.18, dict(body, front="flood_light"), skip=("bottom",))
        mb.box(x0 - 0.12, x0 + 0.05, HY + t - 0.25, HY + t + 0.25, zr, zr + 0.18, dict(body, right="flood_light"), skip=("bottom",))
        mb.box(x1 - 0.05, x1 + 0.12, HY + t - 0.25, HY + t + 0.25, zr, zr + 0.18, dict(body, left="flood_light"), skip=("bottom",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = HX + sx * (HS + 0.03), HY + sy * (HS + 0.03)
            mb.box(x - 0.09, x + 0.09, y - 0.09, y + 0.09, zr, zr + 0.2, "obst_light", skip=("bottom",))
    mx, my, zn = x1 + NET - 0.25, y0 - NET + 0.25, HZT - 0.02
    mb.box(mx - 0.04, mx + 0.04, my - 0.04, my + 0.04, zn, zn + 2.8, "crown_white", skip=("bottom", "top"))
    mb.box(mx - 0.08, mx + 0.08, my - 0.08, my + 0.08, zn + 2.8, zn + 3.0, "obst_light", skip=("bottom",))
    mb.box(mx + 0.04, mx + 0.75, my - 0.14, my + 0.14, zn + 2.3, zn + 2.6, "windsock", skip=("left",))
    mb.box(mx + 0.75, mx + 1.25, my - 0.09, my + 0.09, zn + 2.35, zn + 2.55, "windsock", skip=("left",))


def heli_access(mb):
    """Switchback steel access stair from main roof to West platform."""
    ys, yn, n = HY - 4.5, HY + 3.0, 20
    zt = HZT - 0.02
    zm = (H + zt) / 2
    tr, ri = (yn - ys) / n, (zm - H) / n
    for (xa, xb), y0, z0, dy in (((PX0 - 2.2, PX0 - 1.15), ys, H, 1), ((PX0 - 1.05, PX0), yn, zm, -1)):
        for i in range(n):
            ya, yb = sorted((y0 + dy * i * tr, y0 + dy * (i + 1) * tr))
            ztop = z0 + (i + 1) * ri
            mb.box(xa, xb, ya + 0.02, yb - 0.02, ztop - 0.05, ztop, "grating")
        y1, z1 = y0 + dy * n * tr, z0 + n * ri
        for x in (xa + 0.08, xb - 0.08):
            prism(mb, (x, y0, z0 - 0.15), (x, y1, z1 - 0.15), 0.12, "crown_white")
        xo = xa if dy > 0 else xb
        prism(mb, (xo, y0, z0 + 0.95), (xo, y1, z1 + 0.95), 0.05, "railing")
        for f in (0.1, 0.5, 0.9):
            yy, zz = y0 + dy * f * (n * tr), z0 + f * n * ri
            mb.box(xo - 0.02, xo + 0.02, yy - 0.02, yy + 0.02, zz, zz + 0.95, "railing", skip=("bottom",))
    mb.box(PX0 - 2.2, PX0, yn, yn + 1.2, zm - 0.15, zm, "grating")
    mb.box(PX0 - 1.05, PX0, HY - HS, ys, zt - 0.15, zt, "grating", skip=("right",))
    for x, y, z in ((PX0 - 2.15, yn + 1.1, zm), (PX0 - 0.05, yn + 1.1, zm), (PX0 - 0.3, HY - HS + 0.4, zt)):
        mb.box(x - 0.08, x + 0.08, y - 0.08, y + 0.08, H, z - 0.15, "crown_white", skip=("bottom", "top"))


def roof_crown(mb, stage):
    """105 iconic crown: green-glazed sloped roof conservatory/skylight structure
    running along main ridge, plus rooftop helipad on eastern deck (photos/site.jpg, view_top_far_w.png)."""
    # 1. Base plinth (set in 0.15 m from roof edges)
    mb.box(CROWN_X0 + 0.15, CROWN_X1 - 0.15, CROWN_Y0 + 0.2, CROWN_Y1 - 0.2, H, CROWN_Z0, "pale", skip=("bottom",))

    # 2. Sloped Glass Conservatory
    # Ridge at y = (CROWN_Y0 + CROWN_Y1) / 2
    ym = (CROWN_Y0 + CROWN_Y1) / 2.0
    # North slope: from (x, CROWN_Y0, CROWN_Z_EAVES) up to (x, ym, CROWN_Z_APEX)
    q_north = [(CROWN_X0 - 0.1, CROWN_Y0, CROWN_Z_EAVES), (CROWN_X1 + 0.1, CROWN_Y0, CROWN_Z_EAVES),
               (CROWN_X1 + 0.1, ym, CROWN_Z_APEX), (CROWN_X0 - 0.1, ym, CROWN_Z_APEX)]
    mb.rect(q_north, "crown_glass")

    # South slope: from (x, ym, CROWN_Z_APEX) down to (x, CROWN_Y1, CROWN_Z_EAVES)
    q_south = [(CROWN_X0 - 0.1, ym, CROWN_Z_APEX), (CROWN_X1 + 0.1, ym, CROWN_Z_APEX),
               (CROWN_X1 + 0.1, CROWN_Y1, CROWN_Z_EAVES), (CROWN_X0 - 0.1, CROWN_Y1, CROWN_Z_EAVES)]
    mb.rect(q_south, "crown_glass")

    # West and East gable walls using solid boxes up to CROWN_Z_APEX (completely covers the gable opening)
    mb.box(CROWN_X0 + 0.05, CROWN_X0 + 0.35, CROWN_Y0 + 0.25, CROWN_Y1 - 0.25, CROWN_Z0, CROWN_Z_APEX, "crown_white", skip=("bottom",))
    mb.box(CROWN_X1 - 0.35, CROWN_X1 - 0.05, CROWN_Y0 + 0.25, CROWN_Y1 - 0.25, CROWN_Z0, CROWN_Z_APEX, "crown_white", skip=("bottom",))

    # Vertical clerestory walls
    mb.box(CROWN_X0 + 0.4, CROWN_X1 - 0.4, CROWN_Y0 + 0.25, CROWN_Y0 + 0.45, CROWN_Z0, CROWN_Z_EAVES, "crown_glass", skip=("bottom", "top"))
    mb.box(CROWN_X0 + 0.4, CROWN_X1 - 0.4, CROWN_Y1 - 0.45, CROWN_Y1 - 0.25, CROWN_Z0, CROWN_Z_EAVES, "crown_glass", skip=("bottom", "top"))

    # Eaves horizontal soffit underside closure (prevents -10 deg upward rays seeing roof backface)
    q_north_soffit = [(CROWN_X0 - 0.1, CROWN_Y0 + 0.45, CROWN_Z_EAVES), (CROWN_X1 + 0.1, CROWN_Y0 + 0.45, CROWN_Z_EAVES),
                      (CROWN_X1 + 0.1, CROWN_Y0, CROWN_Z_EAVES), (CROWN_X0 - 0.1, CROWN_Y0, CROWN_Z_EAVES)]
    mb.rect(q_north_soffit, "crown_white")

    q_south_soffit = [(CROWN_X0 - 0.1, CROWN_Y1, CROWN_Z_EAVES), (CROWN_X1 + 0.1, CROWN_Y1, CROWN_Z_EAVES),
                      (CROWN_X1 + 0.1, CROWN_Y1 - 0.45, CROWN_Z_EAVES), (CROWN_X0 - 0.1, CROWN_Y1 - 0.45, CROWN_Z_EAVES)]
    mb.rect(q_south_soffit, "crown_white")

    # Ridge cap
    mb.box(CROWN_X0 - 0.1, CROWN_X1 + 0.1, ym - 0.2, ym + 0.2, CROWN_Z_APEX - 0.1, CROWN_Z_APEX + 0.2, "crown_white")

    # Aviation obstruction lights on crown roof apex
    mb.box(CROWN_X0 + 0.5, CROWN_X0 + 0.8, ym - 0.15, ym + 0.15, CROWN_Z_APEX + 0.2, CROWN_Z_APEX + 0.6, "obst_light", skip=("bottom",))
    mb.box(CROWN_X1 - 0.8, CROWN_X1 - 0.5, ym - 0.15, ym + 0.15, CROWN_Z_APEX + 0.2, CROWN_Z_APEX + 0.6, "obst_light", skip=("bottom",))

    # 3. Helipad Structure (103-style high detail)
    n = (32, 24, 12)[stage]
    # Core column from roof up to underside
    ring(mb, HX, HY, HCORE, H, HCORE, HZ0, "crown_white", n)
    # Sloped square underside
    ring(mb, HX, HY, 2.0, HZ0, RC, HZ1, "deck_under", 4, rot=SQ)
    # Apex cap
    q = K.up_quad([(HX - 1.41, HY - 1.41, HZ0), (HX + 1.41, HY - 1.41, HZ0),
                   (HX + 1.41, HY + 1.41, HZ0), (HX - 1.41, HY + 1.41, HZ0)])
    mb.rect(q[::-1], "deck_under")
    # Deck edge
    ring(mb, HX, HY, RC, HZ1, RC, HZT, "crown_white", 4, rot=SQ)
    # Deck top ring and center quad
    ring(mb, HX, HY, RC, HZT, 1.414, HZT, "deck", 4, rot=SQ)
    q_center = K.up_quad([(HX - 1.0, HY - 1.0, HZT), (HX + 1.0, HY - 1.0, HZT),
                          (HX + 1.0, HY + 1.0, HZT), (HX - 1.0, HY + 1.0, HZT)])
    mb.rect(q_center[::-1], "deck")

    # Green pad on top
    mb.box(HX - 4.4, HX + 4.4, HY - 4.4, HY + 4.4, HZT, HZT + 0.03, "heli_green", skip=("bottom",))

    if stage < 2:
        heli_underside(mb, stage)
        zt = HZT + 0.03
        # Border box around pad and 'H' marking
        for x0, x1, y0, y1 in ((-4.3, -4.15, -4.3, 4.3), (4.15, 4.3, -4.3, 4.3),
                               (-4.15, 4.15, -4.3, -4.15), (-4.15, 4.15, 4.15, 4.3),
                               (-1.2, -0.95, -1.6, 1.6), (0.95, 1.2, -1.6, 1.6),
                               (-0.95, 0.95, -0.12, 0.12)):
            mb.box(HX + x0, HX + x1, HY + y0, HY + y1, zt, zt + 0.03, "heli_white", skip=("bottom",))
        # 32-segment touchdown circle
        for i in range(32):
            a, b = 2 * math.pi * i / 32, 2 * math.pi * (i + 1) / 32
            mb.rect([(HX + r * math.cos(t), HY + r * math.sin(t), zt + 0.04)
                     for r, t in ((2.7, a), (2.7, b), (2.58, b), (2.58, a))], "heli_white")

    if stage == 0:
        # Safety railing (height 0.9 m)
        ring(mb, HX, HY, RC + 0.07, HZT, RC + 0.07, HZT + 0.9, "railing", 4, rot=SQ)
        ring(mb, HX, HY, RC + 0.02, HZT, RC + 0.02, HZT + 0.9, "railing", 4, rot=SQ, flip=True)
        ring(mb, HX, HY, RC + 0.07, HZT + 0.9, RC + 0.02, HZT + 0.9, "railing", 4, rot=SQ)
        heli_access(mb)

    if stage < 2:
        heli_net(mb)
        heli_lights(mb, stage)




# ==============================================================================
# ENTRANCE PORCH
# ==============================================================================
EY = -3.95
EZ0, EZB, EZC, EZT = 3.8, 4.65, 5.45, 5.85
ST_N, ST_R, ST_T = 7, 0.15, 0.36
PORTICO_X0, PORTICO_X1 = 7.5, 16.0


def entrance(mb, stage):
    """105 entrance porch (photos/view_nw_base.png, view_n_base.png):
    Grand pink granite right pier with '105' numeral, dark granite left portal frame,
    EXLLU TOWER canopy band with clerestory strip, 7 stone stair steps, and 5-bar safety railings."""
    ZS = EZT - 0.2
    # Canopy ceiling & pale fascia
    mb.box(PORTICO_X0, PORTICO_X1, EY, 0, EZ0, ZS, dict(front="pale", right="pale", left="pale", bottom="soffit"),
           skip=("back", "top"))

    # Left dark granite pier
    mb.box(PORTICO_X0 - 0.1, PORTICO_X0 + 1.1, EY - 0.1, EY + 1.1, 0, ZS, "stone_trim", skip=("bottom", "top"))

    # Right massive pink granite pier (view_nw_base.png: 105 numeral on both front and side)
    mb.box(14.2, PORTICO_X1 + 0.2, EY - 0.2, EY + 1.8, 0, ZS,
           dict(front="pier_pink", right="pier_pink", left="stone_trim", default="pier_pink"),
           skip=("bottom", "top"))

    # Dark stone roof slab over piers up to tower facade (y=0)
    mb.box(PORTICO_X0 - 0.2, PORTICO_X1 + 0.3, EY - 0.2, 0.0, ZS, EZT, dict(top="roof", default="stone_trim"))

    if stage < 2:
        # Clerestory strip and EXLLU TOWER fascia
        for axis, c, s, a0, a1 in (("y", EY, -1, PORTICO_X0 + 1.1, 14.2),
                                   ("x", PORTICO_X1, 1, EY + 1.8, 0.0),
                                   ("x", PORTICO_X0, -1, EY + 1.1, 0.0)):
            K.paint(mb, axis, c, s, a0, a1, EZC, ZS, "stone", layer=2)
            K.paint(mb, axis, c, s, a0 + 0.2, a1 - 0.2, EZB + 0.08, EZC - 0.08, "clerestory", layer=2)
            K.paint(mb, axis, c, s, a0, a1, EZB, EZB + 0.08, "frame", layer=3)

        # Stairs & landing
        yl = EY + ST_N * ST_T
        for i in range(ST_N):
            y0 = EY + i * ST_T
            mb.box(PORTICO_X0 + 1.1, 14.2, y0, y0 + ST_T, 0, ST_R * (i + 1), "canopy",
                   skip=("bottom", "back", "left", "right"))
        zl = ST_N * ST_R
        mb.box(PORTICO_X0 + 1.1, 14.2, yl, 0, 0, zl, "canopy", skip=("bottom", "back", "left", "right"))
        # Vestibule entrance doors at facade
        mb.box(PORTICO_X0 + 1.1, 14.2, -0.05, 0.0, zl, EZ0, {"front": "vestibule", "default": "stone_trim"},
               skip=("bottom", "top", "back", "left", "right"))

        # Safety railings (5 bars)
        ya = EY + 0.2
        rail_z = lambda y: ST_R + (y - ya) / (yl - ya) * (zl - ST_R)
        # Left handrail
        xl = PORTICO_X0 + 1.2
        for dz in (0.9, 0.45):
            prism(mb, (xl, ya, dz + rail_z(ya)), (xl, yl, dz + rail_z(yl)), 0.05, "railing")
            prism(mb, (xl, yl, dz + zl), (xl, -0.05, dz + zl), 0.05, "railing")
        # Right safety railing along open portico side
        xr = 14.15
        for dz in (0.90, 0.72, 0.54, 0.36, 0.18):
            prism(mb, (xr, ya, dz + rail_z(ya)), (xr, yl, dz + rail_z(yl)), 0.04 if dz < 0.9 else 0.05, "railing")
            prism(mb, (xr, yl, dz + zl), (xr, 0.0, dz + zl), 0.04 if dz < 0.9 else 0.05, "railing")


def terrace(mb, stage):
    """Terrace to the left of portico (photos/view_nw_base.png)."""
    mb.box(-3.5, PORTICO_X0 - 0.2, -1.8, 0, 0, ST_N * ST_R, dict(top="canopy", default="stone_trim"),
           skip=("back", "bottom", "right"))
    tz = ST_N * ST_R
    for dz in (0.18, 0.36, 0.54, 0.72, 0.9):
        prism(mb, (-3.4, -1.72, tz + dz), (PORTICO_X0 - 0.2, -1.72, tz + dz), 0.04 if dz < 0.9 else 0.05, "railing")


# ==============================================================================
# MAIN BUILDING ASSEMBLY
# ==============================================================================
def build(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    wing = dict(front="stone", back="pale", left="stone", right="stone", top="roof", bottom="stone")

    # Main tower mass: wings and central recess
    mb.box(-X, -RX, 0, D, 0, H, wing, skip=("bottom",))
    mb.box(-RX, RX, RD, D, 0, H, dict(front="stone", back="pale", top="roof"), skip=("left", "right", "bottom"))
    mb.box(RX, X, 0, D, 0, H, wing, skip=("bottom",))

    # Dark granite base up to PALE_F_LEFT (floor 6) and PALE_F_RIGHT (floor 8)
    # Left wing upper floors pale
    K.paint(mb, "y", 0, -1, -X, -RX, zf(PALE_F_LEFT), H, "pale")
    # Right wing upper floors pale (above floor 8)
    K.paint(mb, "y", 0, -1, RX, X, zf(PALE_F_RIGHT), H, "pale")

    # Side walls: East side (-X) and West side (+X)
    K.paint(mb, "x", -X, -1, 0, D, zf(PALE_F_LEFT), H, "pale")
    K.paint(mb, "x", X, 1, 0, D, zf(PALE_F_RIGHT), H, "pale")

    # Back wall: upper floors pale
    K.paint(mb, "y", D, 1, -X, X, zf(PALE_F_LEFT), H, "pale")

    # Brand emblem band on the west top face (photos/view_top_far_w.png: EXLLU TOWER)
    # Positioned at y 4.2..5.8 (solid wall area between windows) to avoid WIN_BLOCKED
    if stage < 2:
        mb.box(X, X + 0.08, 4.3, 5.7, zf(46), zf(49), "brand_gold", skip=("left", "top", "bottom"))

    # Projecting balcony ledges on the west face (photos/view_w_full.png, view_top_far_w.png)
    # Stepped slabs protruding every floor on +x face
    if stage < 2:
        for f in range(2, NF):
            z = zf(f)
            mb.box(X, X + LEDGE_P, WEST_LEDGE_Y0, WEST_LEDGE_Y1, z, z + LEDGE_T, "stone_trim",
                   skip=("left", "top" if f == NF - 1 else ()))

    # Roof parapet
    PH = H + 1.4
    mb.box(-X, -RX, 0, 0.35, H, PH, "pale", skip=("bottom",))
    mb.box(RX, X, 0, 0.35, H, PH, "pale", skip=("bottom",))
    mb.box(-X, -X + 0.35, 0.35, D - 0.35, H, PH, "pale", skip=("bottom", "front", "back"))
    mb.box(X - 0.35, X, 0.35, D - 0.35, H, PH, "pale", skip=("bottom", "front", "back"))
    mb.box(-X, X, D - 0.35, D, H, PH, "pale", skip=("bottom",))

    # Corner obstruction lights
    if stage == 0:
        for sx in (-1, 1):
            for sy, yc in ((-1, 0.2), (1, D - 0.2)):
                xc = sx * (X - 0.2)
                mb.box(xc - 0.12, xc + 0.12, yc - 0.12, yc + 0.12, PH, PH + 0.25, "obst_light", skip=("bottom",))

    # Roof Crown & Helipad
    roof_crown(mb, stage)

    # Entrance Porch & Terrace
    entrance(mb, stage)
    if stage < 2:
        terrace(mb, stage)

    # Windows
    if stage == 0:
        ground_floor(mb, stage)
        for f in range(1, NF):
            floor_facade(mb, stage, f)

    return mb


main = build(0)
lod1 = build(1)
lod2 = build(2)

K.export_asset("HighriseTower105", 1, dict(main=main, lod1=lod1, lod2=lod2, windows=WS),
               A, K.out_dir_from_argv("output"))
