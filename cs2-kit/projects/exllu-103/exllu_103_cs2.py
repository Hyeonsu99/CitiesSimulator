"""Tower 103: 50-floor slab tower with a front recess, per-floor stone ledges and a rooftop helipad.

Custom generator (replaces the generic-spec version kept in work/exllu_103_cs2.v1_generic.py).
Evidence: photos/user-01..06 (see work/observations.json). Dimensions not in TASK are estimated.
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

W, D, FH, NF = 32.0, 21.0, 2.94, 50          # TASK: 32 x 21 m, 2.94 m, 50 floors
GH = 5.24                                     # lobby storey: raised so the helipad rail top = 160.0 m (research)
H = GH + FH * (NF - 1)                        # 149.3
TOPG = 41                                     # floors >= TOPG: dark glass corner bays (user-02/05)


def zf(f):
    """Floor level of storey f (0 = lobby)."""
    return 0.0 if f == 0 else GH + (f - 1) * FH

X = W / 2
RX, RD = 5.5, 2.0                             # front recess half-width / depth (estimated)
PIL = RD                                      # left-wing pilotis back wall flush with the recess (user-03, estimated)
LEDGE_P, LEDGE_T = 0.55, 0.28                 # per-floor ledge projection / thickness (estimated; user-07: ~2x thickness out, ~1/10 storey)
SILL, HEAD = 0.75, 2.45                       # window sill / head above floor (estimated)

def granite(ctx, cols, rows, darken, speck):
    """Cladding slabs (joints) + granite speckle + slight slab-to-slab tone shift."""
    ctx.joints(cols=cols, rows=rows, width_m=0.008, depth=1.0, stagger=0.0, darken=darken, tone=4.0)
    ctx.rgb += (ctx.rng.normal(0, speck, (ctx.h, ctx.w)).astype("float32"))[..., None]
    ctx.rgb += ctx.noise(24, speck * 0.6, 3, seed=5)[..., None]


def glass_mullions(ctx):
    """Vertical mullion line at each tile edge + slight sky gradient (floor lines come from the ledges)."""
    mx, _ = ctx.meters()
    d = (mx < 0.03) | (mx > ctx.tile[0] - 0.03)
    ctx.rgb[d] *= 0.55
    ctx.rgb += (ctx.v * 10.0)[..., None]


def window_glass(ctx):
    """Window cell: green-tinted glass (photos), sky reflection, diagonal glint, curtains, ~30 % lit at night.
    Slots follow WindowSet.build's layout (5x5 grid, n x n slots per cell)."""
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
    h = (sid * 2654435761) % 1000 / 1000.0          # stable per-slot random
    ctx.rgb[...] = np.array([68, 110, 110], np.float32) + ((h - 0.5) * 16)[..., None]
    ctx.rgb += (fv * 42)[..., None]                   # sky reflection, brighter towards the top
    m = (fu * 0.7 + fv) % 1.0
    ctx.rgb += (((m > 0.30) & (m < 0.37)) * 22.0)[..., None]   # glint streak
    curt = (h * 7 % 1.0) < 0.45
    cmask = curt & ((fu < 0.13) | (fu > 0.87))
    ctx.rgb[cmask] = ctx.rgb[cmask] * 0.35 + np.array([200, 190, 170], np.float32) * 0.65
    lit = ((h * 13) % 1.0) < 0.3
    ctx.emis[...] = np.where(lit, 1.0, 0.0)
    ctx.gloss[...] = 0.92


def mesh_grid(ctx, n, w, col):
    """Steel mesh / grating: n x n bar grid of relative width w per tile."""
    m = ((ctx.u * n) % 1.0 < w) | ((ctx.v * n) % 1.0 < w)
    ctx.rgb[m] = np.array(col, np.float32)


OBS_GH = 3.65                # observatory glass height between plinth (0.6) and coping (0.35); see observatory()


def obs_glass(ctx):
    """Observatory curtain wall panel (1.2 m x full height): thin frame, transom at 2.6 m, sky reflection brighter
    towards the top, lit interior at night (roof.jpg: the sibling glass crown glows)."""
    mx, mz = ctx.meters()
    ctx.rgb += (ctx.v * 46.0 - 14.0)[..., None]
    fr = (mx < 0.035) | (mx > ctx.tile[0] - 0.035) | (mz < 0.05) | (mz > ctx.tile[1] - 0.05) |          ((mz > 2.58) & (mz < 2.64))
    ctx.rgb[fr] = np.array([210, 214, 212], np.float32)
    ctx.emis[...] = np.where(fr, 0.0, np.where(mz < 2.58, 0.55, 0.3))
    ctx.gloss[...] = np.where(fr, 0.5, 0.92)


def skylight(ctx):
    """Skylight glass: thin grey frame per 1.8 m pane, sky reflection gradient."""
    ctx.rgb += (ctx.v * 30.0 - 8.0)[..., None]
    m = (ctx.u < 0.025) | (ctx.u > 0.975) | (ctx.v < 0.025) | (ctx.v > 0.975)
    ctx.rgb[m] = np.array([150, 156, 160], np.float32)
    ctx.gloss[...] = np.where(m, 0.4, 0.93)


TEX = {  # tile = one 2.4 m x one storey, so joints line up with floors
    "stone": dict(tile=(2.4, FH), px=256, painter=lambda c: granite(c, 2, 4, 0.3, 7.0)),
    "pale": dict(tile=(2.4, FH), px=256, painter=lambda c: granite(c, 2, 3, 0.12, 2.5)),
    "dark_glass": dict(tile=(1.35, FH), px=128, painter=lambda c: glass_mullions(c)),
    "grey_stone": dict(tile=(2.4, FH), px=256, painter=lambda c: granite(c, 2, 4, 0.18, 4.0)),
    "window": dict(px=1024, painter=window_glass, emissive=(255, 205, 150)),
    "pier_pink": dict(tile=(1.2, 1.2), px=128, painter=lambda c: granite(c, 1, 2, 0.2, 9.0)),
    "crown_glass": dict(tile=(1.2, OBS_GH), px=128, painter=lambda c: obs_glass(c), emissive=(255, 228, 185)),
    "obs_roof": dict(tile=(1.8, 1.8), px=128, painter=lambda c: skylight(c)),
    "heli_net": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 4, 0.10, (178, 182, 184))),
    "grating": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 12, 0.25, (70, 72, 74))),
    "heli_light": dict(px=32, painter=lambda c: c.emis.__setitem__(Ellipsis, 1.0), emissive=(110, 255, 140)),
    "under_light": dict(px=32, painter=lambda c: c.emis.__setitem__(Ellipsis, 1.0), emissive=(255, 214, 160)),
}

A = K.Atlas(size=4096, pad=16)
for name, color, metal, gloss, px in (
        ("stone", (88, 82, 80), 0.0, 0.35, 128),        # dark warm granite (user-02/03/05)
        ("stone_trim", (84, 78, 77), 0.0, 0.35, 64),    # ledges/piers: same stone, untiled (no tile splits)
        ("pale", (224, 222, 214), 0.0, 0.3, 128),       # pale centre panels
        ("crown_white", (232, 233, 230), 0.1, 0.4, 64), # helipad core / rim (user-01)
        ("deck_under", (62, 66, 70), 0.2, 0.35, 64),    # dark helipad underside (user-01)
        ("crown_glass", (120, 172, 164), 0.5, 0.9, 128), # light green reflective observatory glass (roof.jpg, user-01)
        ("obs_roof", (64, 84, 100), 0.6, 0.92, 128),    # dark blue-grey skylight glass (satellite)
        ("railing", (200, 203, 205), 0.6, 0.5, 64),
        ("dark_glass", (62, 76, 88), 0.5, 0.85, 64),    # top-floor corner glazing spandrels (user-02/05)
        ("frame", (236, 237, 235), 0.3, 0.5, 64),       # white window frames
        ("louver", (230, 231, 229), 0.2, 0.4, 64),      # AC louver panels
        ("louver_back", (58, 60, 62), 0.0, 0.3, 64),
        ("roof", (120, 122, 122), 0.0, 0.3, 64),
        ("deck", (150, 152, 150), 0.0, 0.3, 64),
        ("heli_green", (74, 140, 104), 0.0, 0.25, 64),
        ("heli_white", (232, 234, 226), 0.0, 0.25, 64),
        ("pier_pink", (176, 140, 130), 0.0, 0.4, 128),
        ("canopy", (160, 163, 162), 0.2, 0.45, 128),
        ("glass", (150, 185, 180), 0.0, 0.9, 64),       # _Gls pane over every window (green tint, photos)
        ("grey_stone", (168, 168, 164), 0.0, 0.3, 128), # back base + upper bay (user-01)
        ("pale_trim", (226, 224, 218), 0.0, 0.3, 64),  # back ledges, lower floors (user-01)
        ("grey_trim", (150, 151, 148), 0.0, 0.3, 64),  # back ledges, grey upper bay (user-01)
        ("white_shaft", (240, 240, 236), 0.0, 0.3, 64), # back central shaft (user-01)
        ("heli_net", (72, 76, 80), 0.6, 0.4, 64),       # helideck perimeter safety net (steel mesh)
        ("grating", (128, 132, 134), 0.6, 0.35, 64),    # access platform / stair treads
        ("heli_light", (90, 230, 120), 0.0, 0.6, 32),   # green perimeter lights (emissive)
        ("under_light", (250, 236, 210), 0.0, 0.6, 32), # warm downlights under the deck (roof.jpg sibling at night)
        ("window", (70, 110, 110), 0.0, 0.9, 1024)):
    A.add(name, color=color, ctrl=(0, 0, 0), metal=metal, gloss=gloss, **dict(dict(px=px), **TEX.get(name, {})))

WS = K.WindowSet()
GLS = K.MeshBuilder(A)  # glass panes in front of the _Win quads (main only)


def window(mb, stage, axis, c, s, a0, a1, z0, z1, floor, unit, mull=(), jambs=(True, True)):
    """_Win quad + (main only) projecting white frame, sill and painted mullions/transom.
    jambs=(False, ..) drops the jamb at that end (corner window meeting a corner post)."""
    if stage == 0:
        WS.add_face(axis, c, s, a0, a1, z0, z1, floor=floor, unit=unit)
        GLS.rect(K.face_pts(axis, c + s * 0.025, s, a0, a1, z0, z1), "glass")  # between _Win (2 cm) and mullions (3 cm)
        if jambs[0]:
            K.axbox(mb, axis, c, s, a0 - 0.1, a0, 0, 0.12, z0, z1, "frame", skip=("top", "bottom"))
        if jambs[1]:
            K.axbox(mb, axis, c, s, a1, a1 + 0.1, 0, 0.12, z0, z1, "frame", skip=("top", "bottom"))
        e0, e1 = (0.1 if jambs[0] else 0.0), (0.1 if jambs[1] else 0.0)
        K.axbox(mb, axis, c, s, a0 - e0, a1 + e1, 0, 0.12, z1, z1 + 0.1, "frame")
        K.axbox(mb, axis, c, s, a0 - (0.15 if jambs[0] else 0.0), a1 + (0.15 if jambs[1] else 0.0),
                0, 0.18, z0 - 0.1, z0, "frame")
        for u in mull:  # never at u=0.5 so the window centre stays unblocked
            a = a0 + (a1 - a0) * u
            K.paint(mb, axis, c, s, a - 0.03, a + 0.03, z0, z1, "frame", layer=3)
        zt = z0 + 0.74 * (z1 - z0)
        K.paint(mb, axis, c, s, a0, a1, zt, zt + 0.05, "frame", layer=4)


def louver(mb, stage, axis, c, s, a0, a1, z0, z1):
    if stage == 0:
        K.axbox(mb, axis, c, s, a0, a1, 0, 0.08, z0, z1, "louver")
        n = int((z1 - z0) / 0.3)
        for i in range(1, n):
            z = z0 + i * (z1 - z0) / n
            K.paint(mb, axis, c, s, a0 + 0.08, a1 - 0.08, z - 0.02, z + 0.02, "louver_back", layer=9)


WIDE = (0.2, 0.4, 0.6, 0.8)
CW = 0.15                    # corner window stops this far from the wall corner; a post fills the gap
SIDE_WINS = ((7.4, 10.2, (0.3, 0.7)), (12.0, 14.8, (0.3, 0.7)), (16.4, 20.0, (0.3, 0.7)))  # lobby floor only
# upper floors (user-07/08): front flank = corner window, pale centre y 6.4-14.8 with small windows that change
# per floor + one white panel, back flank = one wide window
SIDE_PALE = (6.4, 14.8)
PALE_F = 7                   # user-07: side centre is dark stone with full-width ledges below this floor (estimated count)
SIDE_LOUVER = (11.45, 12.15)
SIDE_CENTRE = (
    (((7.0, 8.4), (9.9, 11.1), (12.6, 14.0)), SILL),
    (((7.0, 8.8), (10.1, 10.9), (12.6, 14.2)), SILL),
    (((7.0, 7.8), (8.2, 9.0), (10.0, 11.0), (12.6, 14.0)), 1.1),
)
SIDE_BACK = (16.0, 20.2)
# NW side (+x), Naver street view 2025-03 (pano adGlg.., ~47 m WNW): pale above PALE_F with no side ledges,
# full-height dark slot ~9 m from the front corner, pairs of small windows either side of it, wide windows outside
SL0, SL1, SLD = 8.8, 10.4, 1.2   # slot y range / depth (estimated from the panorama)
NW_WINS = ((6.6, 7.4, 1.1, ()), (7.8, 8.5, 1.1, ()), (10.7, 11.4, 1.1, ()), (11.8, 12.5, 1.1, ()),
           (13.0, 15.6, SILL, (0.3, 0.7)), (16.4, 20.2, SILL, WIDE))
# back (user-01, read as the back elevation): flat bay x < 2 with mixed wide/narrow windows,
# white shaft x 2..5 (no windows), balcony bay x > 5 with wide multi-pane windows
BACK_WINS = ((-15.2, -12.2, (0.3, 0.7)), (-11.4, -7.4, WIDE), (-6.6, -5.4, ()), (-4.4, -0.8, (0.3, 0.7)),
             (5.6, 9.6, (0.3, 0.7)), (10.4, 15.2, WIDE))
# front centre (recess back wall): street view sv-front + user-03 show the same windows on every floor with a
# ledge per floor (user-05, the old source, is the SE side). Centre 3-pane window between the louvers,
# 2-pane windows outside them (widths estimated)
CENTRE = ((-4.6, -2.8, (0.3, 0.7)), (-1.2, 1.2, (1 / 3, 2 / 3)), (2.8, 4.6, (0.3, 0.7)))
CENTRE_SEQ = (0, 1, 0, 2, 0, 0, 1, 2, 0, 1, 0, 0, 2)   # SE side centre order (estimated)


def corner_bay(mb, stage, sgn, z, f, u):
    """Front corner of a wing: one window wrapping round the corner (user-04), dark glass on top floors (user-02/05)."""
    top = f >= TOPG
    z0, z1 = (z + 0.3, z + FH - 0.3) if top else (z + SILL, z + HEAD)
    mull = (0.2, 0.4, 0.6, 0.8) if not top else (0.12, 0.26, 0.4, 0.6, 0.74, 0.88)
    # front face: corner end is the outer end (a1 for the right wing, a0 for the left)
    a0, a1 = (-(X - CW), -10.4) if sgn < 0 else (10.4, X - CW)
    window(mb, stage, "y", 0, -1, a0, a1, z0, z1, f, u, mull,
           jambs=(sgn > 0, sgn < 0))
    # side face: a = y, corner end is a0 (y = 0)
    window(mb, stage, "x", sgn * X, sgn, CW, 5.4, z0, z1, f, u + 1, (0.3, 0.7) if not top else (0.25, 0.75),
           jambs=(False, True))
    if stage == 0:
        K.corner_post(mb, sgn * X, 0.0, sgn, -1, 0.12, z0, z1, "frame")
    return u + 2


def floor_facade(mb, stage, f):
    """Windows and louvers of one upper floor f (f >= 1)."""
    z = zf(f)
    z0, z1, u = z + SILL, z + HEAD, 0
    for sgn in (-1, 1):  # front wings, mirrored
        a = lambda p, q: (min(sgn * p, sgn * q), max(sgn * p, sgn * q))
        u = corner_bay(mb, stage, sgn, z, f, u)
        louver(mb, stage, "y", 0, -1, *a(8.4, 9.4), z + 0.4, z1)
        window(mb, stage, "y", 0, -1, *a(6.0, 7.4), z0, z1, f, u); u += 1
        # recess side wall (left wing faces +x, right wing faces -x)
        window(mb, stage, "x", sgn * RX, -sgn, 0.6, 1.5, z0, z1, f, u); u += 1
        louver(mb, stage, "y", RD, -1, *a(1.4, 2.3), z + 0.4, z1)
    for a0, a1, m in CENTRE:
        window(mb, stage, "y", RD, -1, a0, a1, z0, z1, f, u, m); u += 1
    swins, ssill = SIDE_CENTRE[CENTRE_SEQ[(f + 5) % len(CENTRE_SEQ)]]
    for a0, a1 in swins:                                     # SE side (user-07/08)
        window(mb, stage, "x", -X, -1, a0, a1, z + ssill, z1, f, u); u += 1
    louver(mb, stage, "x", -X, -1, *SIDE_LOUVER, z + 0.4, z1)
    window(mb, stage, "x", -X, -1, *SIDE_BACK, z0, z1, f, u, WIDE); u += 1
    for a0, a1, sl, m in NW_WINS:                            # NW side (street view)
        window(mb, stage, "x", X, 1, a0, a1, z + sl, z1, f, u, m); u += 1
    for a0, a1, m in BACK_WINS:
        window(mb, stage, "y", D, 1, a0, a1, z0, z1, f, u, m); u += 1


def ground_floor(mb, stage):
    z0, z1, u = 0.3, GH - 0.6, 0          # double-height lobby glazing
    zs0, zs1 = SILL, GH - 0.8
    window(mb, stage, "y", RD, -1, -4.6, 4.6, z0, z1, 0, u, (0.2, 0.4, 0.6, 0.8)); u += 1
    window(mb, stage, "y", 0, -1, 6.0, 15.4, z0, z1, 0, u, (0.2, 0.4, 0.6, 0.8)); u += 1
    for a0, a1 in ((-14.6, -11.4), (-10.1, -6.9)):  # either side of the middle pilotis column
        window(mb, stage, "y", PIL, -1, a0, a1, z0, z1, 0, u, (0.3, 0.7)); u += 1
    window(mb, stage, "x", X, 1, 1.0, 5.4, zs0, zs1, 0, u, (0.3, 0.7)); u += 1   # right side front bay
    for sgn in (-1, 1):
        for a0, a1, m in SIDE_WINS:
            window(mb, stage, "x", sgn * X, sgn, a0, a1, zs0, zs1, 0, u, m); u += 1
    for a0, a1, m in BACK_WINS:
        window(mb, stage, "y", D, 1, a0, a1, zs0, zs1, 0, u, m); u += 1


def ledges(mb, z, p, t, back="stone_trim", side_gap=False):
    """Ring ledge round the tower except the recess; touching faces skipped (no coplanar pairs).
    side_gap: the side ledges stop at the pale side centre (user-07: flanks only above PALE_F)."""
    mb.box(-RX, RX, RD - p, RD, z, z + t, "stone_trim", skip=("back", "left", "right"))   # across the recess (sv-front)
    mb.box(-X - p, -RX, -p, 0, z, z + t, "stone_trim", skip=("back",))
    if side_gap:   # SE: flanks only; NW: no side ledge (street view), front/back ledges end in a corner piece
        mb.box(RX, X, -p, 0, z, z + t, "stone_trim", skip=("back", "right"))
        mb.box(X, X + p, -p, 0, z, z + t, "stone_trim", skip=("left",))
        for y0, y1, ends in ((0, SIDE_PALE[0], ("front",)), (SIDE_PALE[1], D, ())):
            mb.box(-X - p, -X, y0, y1, z, z + t, "stone_trim", skip=ends + ("right",))
        mb.box(SHX1, X, D, D + p, z, z + t, back, skip=("front", "left", "right"))
        mb.box(X, X + p, D, D + p, z, z + t, back, skip=("left",))
        return
    mb.box(RX, X + p, -p, 0, z, z + t, "stone_trim", skip=("back",))
    mb.box(-X - p, -X, 0, D, z, z + t, "stone_trim", skip=("front", "right"))
    mb.box(X, X + p, 0, D, z, z + t, "stone_trim", skip=("front", "back", "left"))
    mb.box(SHX1, X + p, D, D + p, z, z + t, back, skip=("front", "left"))  # back: balcony bay only (user-01)


def prism(mb, p0, p1, w, region):
    """Square strut of width w from p0 to p1 (4 side quads; ends are buried in core / deck)."""
    d = [b - a for a, b in zip(p0, p1)]
    L = math.sqrt(sum(v * v for v in d))
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


def ring(mb, cx, cy, r0, z0, r1, z1, region, n, flip=False, rot=0.0):
    """Band of n quads between polygon (r0, z0) and polygon (r1, z1) (corner radius r, first corner at rot);
    normal outward/up unless flip. n=4, rot=45 deg gives an axis-aligned square."""
    for i in range(n):
        a, b = rot + 2 * math.pi * i / n, rot + 2 * math.pi * (i + 1) / n
        q = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0), (cx + r0 * math.cos(b), cy + r0 * math.sin(b), z0),
             (cx + r1 * math.cos(b), cy + r1 * math.sin(b), z1), (cx + r1 * math.cos(a), cy + r1 * math.sin(a), z1)]
        mb.rect(q[::-1] if flip else q, region)


# Crown. user-09 aerial (labelled 103): long axis NW-SE, +x = NW end. Square helipad deck ~16 m at ~36 % from
# the NW end; dark glass grid (observatory) shows round the deck on the NW and SW sides; white steel frame at
# the SE edge of the deck; SE half is plain roof. user-01: white core + V struts under a dark sloped underside.
# Research: helipad + observatory on each tower, top 160-160.7 m. Sizes estimated.
SHX0, SHX1 = 2.0, 5.0        # back white shaft (user-01); the helipad core rises above it
BAY1 = 12.2                  # back grey bay ends here; pale strip to the corner (street view bC, ~7 m bay)
HX, HY = 4.5, 10.5           # deck centre (aerial: 36 % from the NW end)
HS, HCORE = 6.85, 1.3        # deck half-size (13.7 m, Naver satellite) / core radius
HZ0 = H + 7.2                # underside meets the core
HZ1 = H + 9.2                # underside meets the deck edge
HZT = H + 9.8                # deck top; rail top H + 10.7 = 160.0 m
OX0, OX1, OY0, OY1 = -3.0, 15.2, 3.0, 20.2   # observatory glass box under the deck (aerial)
OZ = H + 4.6                 # observatory roof
SQ = math.pi / 4             # rot for axis-aligned squares
RC = HS * math.sqrt(2)       # deck corner radius


def crown(mb, stage):
    n = (32, 24, 12)[stage]
    ring(mb, HX, HY, HCORE, H, HCORE, HZ0, "crown_white", n)                       # core
    ring(mb, HX, HY, 2.6, HZ0, RC, HZ1, "deck_under", 4, rot=SQ)                   # sloped square underside
    q = K.up_quad([(HX - 1.84, HY - 1.84, HZ0), (HX + 1.84, HY - 1.84, HZ0),
                   (HX + 1.84, HY + 1.84, HZ0), (HX - 1.84, HY + 1.84, HZ0)])
    mb.rect(q[::-1], "deck_under")                                                  # apex cap (core top gap)
    ring(mb, HX, HY, RC, HZ1, RC, HZT, "crown_white", 4, rot=SQ)                   # deck edge
    ring(mb, HX, HY, RC, HZT, 0.85, HZT, "deck", 4, rot=SQ)                        # deck top
    mb.box(HX - 6.0, HX + 6.0, HY - 6.0, HY + 6.0, HZT, HZT + 0.03, "heli_green", skip=("bottom",))
    observatory(mb, stage)
    if stage < 2:
        heli_underside(mb, stage)
        zt = HZT + 0.03
        s = 6.0 / 6.6
        for x0, x1, y0, y1 in ((-6.1, -5.95, -6.1, 6.1), (5.95, 6.1, -6.1, 6.1), (-5.95, 5.95, -6.1, -5.95),
                               (-5.95, 5.95, 5.95, 6.1), (-1.7, -1.4, -2.3, 2.3), (1.4, 1.7, -2.3, 2.3),
                               (-1.4, 1.4, -0.15, 0.15)):
            mb.box(HX + x0 * s, HX + x1 * s, HY + y0 * s, HY + y1 * s, zt, zt + 0.03, "heli_white", skip=("bottom",))
        for i in range(32):
            a, b = 2 * math.pi * i / 32, 2 * math.pi * (i + 1) / 32
            mb.rect([(HX + r * math.cos(t), HY + r * math.sin(t), zt + 0.04)
                     for r, t in ((3.7, a), (3.7, b), (3.58, b), (3.58, a))], "heli_white")
    if stage == 0:
        ring(mb, HX, HY, RC + 0.07, HZT, RC + 0.07, HZT + 0.9, "railing", 4, rot=SQ)        # safety rail, both faces
        ring(mb, HX, HY, RC + 0.02, HZT, RC + 0.02, HZT + 0.9, "railing", 4, rot=SQ, flip=True)
        ring(mb, HX, HY, RC + 0.07, HZT + 0.9, RC + 0.02, HZT + 0.9, "railing", 4, rot=SQ)  # rail top cap
        # white steel frame on the SE (-x) edge of the deck (aerial): posts from the observatory roof
        heli_access(mb)

    if stage < 2:
        heli_net(mb)


NET = 1.5                    # safety net width (user-06 / satellite: light band round the deck; estimated)
PX0 = HX - HS - NET          # access platform outer edge (SE side)


def observatory(mb, stage):
    """Glass observatory under the deck: pale stone plinth, glazing set back 0.15 m, white coping with a gridded
    glass roof, projecting white mullions every 2.4 m (replaces the earlier plain teal box)."""
    zp, zc = H + 0.6, OZ - 0.35
    mb.box(OX0, OX1, OY0, OY1, H, zp, "pale", skip=("bottom",))                               # plinth
    g = 0.15
    mb.box(OX0 + g, OX1 - g, OY0 + g, OY1 - g, zp, zc, "crown_glass", skip=("bottom", "top"))  # glazing
    mb.box(OX0, OX1, OY0, OY1, zc, OZ, dict(top="roof", default="crown_white"))               # coping + roof
    if stage > 1:
        return
    # raised skylight lanterns only where the roof is open to the sky: NW and SW strips beyond the deck (satellite)
    xd, yd, t = HX + HS + 0.25, HY + HS + 0.25, 0.5
    mb.box(xd, OX1 - 0.3, OY0 + 0.3, OY1 - 0.3, OZ, OZ + t, dict(top="obs_roof", default="crown_white"),
           skip=("bottom",))                                                                       # NW lantern
    mb.box(OX0 + 0.8, xd, yd, OY1 - 0.3, OZ, OZ + t, dict(top="obs_roof", default="crown_white"),
           skip=("bottom", "right"))                                                              # SW lantern
    if stage > 0:
        return
    for axis, c, s, a0, a1 in (("y", OY0 + g, -1, OX0 + g, OX1 - g), ("y", OY1 - g, 1, OX0 + g, OX1 - g),
                               ("x", OX0 + g, -1, OY0 + g, OY1 - g), ("x", OX1 - g, 1, OY0 + g, OY1 - g)):
        n = int((a1 - a0) / 2.4)
        for k in range(1, n + 1):
            a = a0 + k * (a1 - a0) / (n + 1)
            K.axbox(mb, axis, c, s, a - 0.06, a + 0.06, 0, 0.14, zp, zc, "crown_white", skip=("top", "bottom"))


def under_z(d):
    """Height of the sloped square underside at Chebyshev distance d from the deck centre."""
    return HZ0 + (HZ1 - HZ0) * (d - 1.84) / (HS - 1.84)


def heli_underside(mb, stage):
    """Underside structure (user-01: white core, struts fanning out from a node on the core under a dark dish;
    roof.jpg: the sibling deck's underside glows at night). Collar node on the core, 8 struts from the collar
    to the underside, 8 white radial ribs hanging under the dark surface, warm downlights between the ribs."""
    zc0, zc1 = OZ + 0.7, OZ + 1.3                                            # collar band on the core
    n = 32 if stage == 0 else 16
    ring(mb, HX, HY, HCORE + 0.18, zc0, HCORE + 0.18, zc1, "crown_white", n)
    ring(mb, HX, HY, HCORE + 0.18, zc1, HCORE, zc1, "crown_white", n)               # collar top
    ring(mb, HX, HY, HCORE + 0.18, zc0, HCORE, zc0, "crown_white", n, flip=True)    # collar bottom
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        c, s = math.cos(a), math.sin(a)
        k = max(abs(c), abs(s))                                              # radius -> Chebyshev distance
        d1 = 0.78 * HS
        prism(mb, (HX + (HCORE + 0.1) * c, HY + (HCORE + 0.1) * s, (zc0 + zc1) / 2),
              (HX + d1 / k * c, HY + d1 / k * s, under_z(d1) + 0.15), 0.42, "crown_white")   # strut
    if stage > 0:
        return
    for i in range(8):                                                       # radial ribs, 0.2 m below the dish
        a = 2 * math.pi * i / 8
        c, s = math.cos(a), math.sin(a)
        k = max(abs(c), abs(s))
        d0, d1 = 2.0, HS - 0.15
        prism(mb, (HX + d0 / k * c, HY + d0 / k * s, under_z(d0) - 0.2),
              (HX + d1 / k * c, HY + d1 / k * s, under_z(d1) - 0.2), 0.22, "crown_white")
    for i in range(8):                                                       # warm downlights between the ribs
        a = 2 * math.pi * (i + 0.5) / 8
        c, s = math.cos(a), math.sin(a)
        d = 4.6
        x, y = HX + d / max(abs(c), abs(s)) * c, HY + d / max(abs(c), abs(s)) * s
        z = under_z(d)
        mb.box(x - 0.3, x + 0.3, y - 0.3, y + 0.3, z - 0.16, z - 0.04, "under_light", skip=("top",))


def heli_net(mb):
    """Perimeter safety net (steel mesh, flat, flush with the deck edge so no gap shows from below) on the NE,
    NW and SW deck edges; a steel grating access platform replaces it on the SE edge (satellite, user-06)."""
    z0, z1 = HZT - 0.19, HZT - 0.02                       # nets and platform share one slab: seamless joins
    xe, y0, y1 = HX + HS, HY - HS, HY + HS
    mb.box(xe, xe + NET, y0 - NET, y1 + NET, z0, z1, "heli_net", skip=("left",))              # NW (+x)
    mb.box(PX0, xe, y1, y1 + NET, z0, z1, "heli_net", skip=("front", "right"))                 # SW (+y)
    mb.box(PX0, xe, y0 - NET, y0, z0, z1, "heli_net", skip=("back", "right"))                  # NE (-y)
    mb.box(PX0, HX - HS, y0, y1, z0, z1, "grating", skip=("right", "front", "back"))


def heli_access(mb):
    """Green perimeter lights and the switchback steel access stair from the main roof to the SE platform."""
    for k in range(7):                                    # perimeter lights, 7 per side, on the grey deck band
        t = -HS + 0.8 + k * (2 * HS - 1.6) / 6
        for x, y in ((HX + t, HY + HS - 0.3), (HX + t, HY - HS + 0.3), (HX + HS - 0.3, HY + t), (HX - HS + 0.3, HY + t)):
            mb.box(x - 0.1, x + 0.1, y - 0.1, y + 0.1, HZT, HZT + 0.1, "heli_light", skip=("bottom",))
    ys, yn, n = HY - 5.6, HY + 3.2, 24                   # flights run along y outside the observatory (x < OX0)
    zt = HZT - 0.02
    zm = (H + zt) / 2
    tr, ri = (yn - ys) / n, (zm - H) / n
    for (xa, xb), y0, z0, dy in (((PX0 - 2.4, PX0 - 1.25), ys, H, 1), ((PX0 - 1.15, PX0), yn, zm, -1)):
        for i in range(n):                               # open treads (gaps keep faces apart)
            ya, yb = sorted((y0 + dy * i * tr, y0 + dy * (i + 1) * tr))
            ztop = z0 + (i + 1) * ri
            mb.box(xa, xb, ya + 0.02, yb - 0.02, ztop - 0.05, ztop, "grating")
        y1, z1 = y0 + dy * n * tr, z0 + n * ri
        for x in (xa + 0.08, xb - 0.08):                 # stringers (faces kept off the tread ends)
            prism(mb, (x, y0, z0 - 0.15), (x, y1, z1 - 0.15), 0.12, "crown_white")
        xo = xa if dy > 0 else xb                        # outer handrail + posts
        prism(mb, (xo, y0, z0 + 0.95), (xo, y1, z1 + 0.95), 0.05, "railing")
        for f in (0.1, 0.5, 0.9):
            yy, zz = y0 + dy * f * (n * tr), z0 + f * n * ri
            mb.box(xo - 0.02, xo + 0.02, yy - 0.02, yy + 0.02, zz, zz + 0.95, "railing", skip=("bottom",))
    mb.box(PX0 - 2.4, PX0, yn, yn + 1.3, zm - 0.15, zm, "grating")                  # mid landing
    mb.box(PX0 - 1.15, PX0, HY - HS, ys, zt - 0.15, zt, "grating", skip=("right",))  # top landing -> platform
    for x, y, z in ((PX0 - 2.35, yn + 1.2, zm), (PX0 - 0.05, yn + 1.2, zm), (PX0 - 0.3, HY - HS + 0.4, zt)):
        mb.box(x - 0.1, x + 0.1, y - 0.1, y + 0.1, H, z - 0.15, "crown_white", skip=("bottom", "top"))  # posts
    for p0, p1 in (((PX0 - 0.3, ys, H), (PX0 - 0.3, yn, zm - 0.4)),          # X bracing under the upper flight
                   ((PX0 - 0.42, yn, H), (PX0 - 0.42, ys, zm - 0.4))):   # second brace offset: no shared plane
        prism(mb, p0, p1, 0.1, "crown_white")


EY = -4.2                    # porch front (user entrance photos; depth estimated)
EZ0, EZB, EZC, EZT = 3.8, 5.0, 5.8, 6.2   # porch soffit / pale band top / clerestory top / cap top (estimated)
ST_N, ST_R, ST_T = 7, 0.15, 0.36          # stair: 7 risers of 0.15 m, 0.4 m treads (counted from the photo)


def entrance(mb, stage):
    """Entrance porch (user entrance photos): deep box canopy whose front and +x faces show a pale panel band,
    a clerestory window strip and a dark stone cap; dark granite left pier, wide pink granite corner pier;
    raised stair between stone cheek walls with steel handrails; recessed dark glass vestibule.
    The "103" numerals and the sign lettering are not modeled (no sign text)."""
    mb.box(7.5, 15.55, EY, 0, EZ0, EZT, dict(front="pale", right="pale", left="stone", top="roof",
                                             bottom="canopy"), skip=("back",))
    mb.box(7.4, 8.6, EY - 0.1, EY + 1.1, 0, EZT + 0.1, "stone_trim", skip=("bottom",))         # left pier
    mb.box(13.7, 15.7, EY - 0.2, EY + 1.8, 0, EZT + 0.3, dict(top="stone_trim", default="pier_pink"),
           skip=("bottom",))                                                                  # corner pier
    if stage == 2:
        return
    for axis, c, s, a0, a1 in (("y", EY, -1, 8.6, 13.7), ("x", 15.55, 1, EY + 1.8, 0.0)):
        K.paint(mb, axis, c, s, a0, a1, EZC, EZT, "stone", layer=2)                           # cap band
        K.paint(mb, axis, c, s, a0 + 0.2, a1 - 0.2, EZB + 0.08, EZC - 0.08, "dark_glass", layer=2)  # clerestory
        K.paint(mb, axis, c, s, a0, a1, EZB, EZB + 0.08, "frame", layer=3)
    yl = EY + ST_N * ST_T                                                                     # landing front
    for i in range(ST_N):                                                                     # steps
        y0 = EY + i * ST_T
        mb.box(8.6, 13.7, y0, y0 + ST_T if i < ST_N - 1 else -1.6, 0, ST_R * (i + 1), "canopy",
               skip=("bottom", "back", "left", "right"))
    zl = ST_N * ST_R
    mb.box(8.6, 13.7, -1.7, -1.6, zl, EZ0, {"front": "glass", "default": "stone_trim"}, skip=("bottom", "top"))
    for x0, x1, y0 in ((8.2, 8.6, EY + 1.1), (13.7, 14.1, EY + 1.8)):                         # cheek walls
        mb.box(x0, x1, y0, -1.6, 0, zl + 0.2, "stone_trim", skip=("bottom", "front"))       # front touches pier
    if stage == 0:
        ya = EY + 0.2
        rail_z = lambda y: ST_R + (y - ya) / (yl - ya) * (zl - ST_R)                           # stair pitch line
        for x in (8.75, 13.55):                                                               # handrails
            for dz in (0.9, 0.45):
                prism(mb, (x, ya, dz + rail_z(ya)), (x, yl, dz + rail_z(yl)), 0.05, "railing")
            for k in range(4):
                yy = ya + k * (yl - ya - 0.1) / 3
                zb = ST_R * min(ST_N, 1 + int((yy - EY) / ST_T))                              # tread under the post
                mb.box(x - 0.03, x + 0.03, yy - 0.03, yy + 0.03, zb, 0.9 + rail_z(yy), "railing", skip=("bottom",))


def build(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    wing = dict(front="stone", back="pale", left="stone", right="stone", top="roof", bottom="stone")
    # body: wings + recessed centre; centre skips its side faces (inside the wings)
    mb.box(-X, -RX, 0, D, GH, H, dict(wing, right="pale"))
    mb.box(-X, -RX, PIL, D, 0, GH, "stone", skip=("top", "bottom"))
    mb.box(-RX, RX, RD, D, 0, H, dict(front="pale", back="pale", top="roof"), skip=("left", "right", "bottom"))
    # right wing split round the NW full-height slot (street view): slot walls dark stone, slot back darker
    rw = dict(wing, left="pale")
    mb.box(RX, X, 0, SL0, 0, H, dict(rw, back="stone"), skip=("bottom",))
    mb.box(RX, X, SL1, D, 0, H, dict(rw, front="stone"), skip=("bottom",))
    mb.box(RX, X, SL0, SL1, 0, GH, rw, skip=("bottom", "front", "back", "left"))
    mb.box(RX, X - SLD, SL0, SL1, GH, H, dict(rw, right="louver_back"), skip=("bottom", "front", "back", "left"))
    # pale strips on the wings beside the recess, dark stone base on the centre (user-03/05)
    for sgn in (-1, 1):
        K.paint(mb, "y", 0, -1, *sorted((sgn * 9.9, sgn * 7.8)), zf(2), H, "pale")
    K.paint(mb, "y", RD, -1, -RX, RX, 0, zf(PALE_F), "stone")   # dark up to PALE_F like the sides (sv-front base view)
    for sgn in (-1, 1):  # top floors: corner bays turn to dark glass (front + side)
        K.paint(mb, "y", 0, -1, *sorted((sgn * X, sgn * 10.2)), zf(TOPG), H, "dark_glass")
    K.paint(mb, "x", -X, -1, 0.0, 5.6, zf(TOPG), H, "dark_glass")              # SE side only (user-07/08)
    K.paint(mb, "x", -X, -1, 15.4, D, zf(TOPG), H, "dark_glass")
    K.paint(mb, "x", -X, -1, *SIDE_PALE, zf(PALE_F), H, "pale")
    K.paint(mb, "x", -X, -1, SIDE_PALE[1], D, zf(PALE_F), zf(TOPG), "pale")   # back flank pale, ledges stay (se_hi)
    for a0, a1 in ((0.0, SL0), (SL1, D)):                                      # NW side all pale (street view)
        K.paint(mb, "x", X, 1, a0, a1, zf(PALE_F), H, "pale")
    # back (user-01): light grey stone base stepping 6 / 12 floors, grey upper balcony bay, white shaft
    # street view (2025-03, SSW): the back base is the same dark granite as the sides, up to PALE_F
    K.paint(mb, "y", D, 1, SHX1, X, 0, zf(PALE_F), "stone")
    K.paint(mb, "y", D, 1, -X, SHX0, 0, zf(PALE_F), "stone")
    K.paint(mb, "y", D, 1, SHX1, BAY1, zf(PALE_F), H, "grey_stone")   # grey bay from the base up (street view bC/bkz)
    mb.box(SHX0, SHX1, D, D + 0.5, 0, H + 1.3, "white_shaft", skip=("bottom", "front"))
    K.paint(mb, "y", D + 0.5, 1, SHX0, SHX1, 0, zf(4), "grey_stone")
    # pilotis columns under the left wing
    # entrance photo 1: wide dark granite corner pier, open bay (no middle column), pale grey column at the end
    mb.box(-X, -X + 1.2, 0, 1.2, 0, GH, "stone_trim", skip=("top", "bottom"))
    mb.box(-6.35, -5.65, 0.15, 0.85, 0, GH, "grey_stone", skip=("top", "bottom"))
    if stage < 2:
        for f in range(1, NF + 1):
            if f == 2:
                ledges(mb, zf(f), 0.6, 0.55, "grey_trim")       # podium band
            elif f == NF:
                ledges(mb, H, 0.5, 0.35, "grey_trim")            # cornice
            else:
                ledges(mb, zf(f), LEDGE_P, LEDGE_T, "grey_trim", f >= PALE_F)
    # parapet (pale crown)
    PH = H + 1.3
    for x0, x1 in ((-X, -RX), (RX, X)):
        mb.box(x0, x1, 0, 0.3, H, PH, "pale", skip=("bottom",))
    mb.box(-RX, RX, RD, RD + 0.3, H, PH, "pale", skip=("bottom", "left", "right"))
    mb.box(-RX - 0.3, -RX, 0.3, RD + 0.3, H, PH, "pale", skip=("bottom", "front"))
    mb.box(RX, RX + 0.3, 0.3, RD + 0.3, H, PH, "pale", skip=("bottom", "front"))
    mb.box(-X, -X + 0.3, 0.3, D - 0.3, H, PH, "pale", skip=("bottom", "front", "back"))
    mb.box(X - 0.3, X, 0.3, D - 0.3, H, PH, "pale", skip=("bottom", "front", "back"))
    mb.box(-X, X, D - 0.3, D, H, PH, "pale", skip=("bottom",))
    crown(mb, stage)
    entrance(mb, stage)
    # windows (WindowSet is shared by all LODs; frames only in main)
    if stage == 0:
        ground_floor(mb, stage)
        for f in range(1, NF):
            floor_facade(mb, stage, f)
    return mb


main = build(0)
lod1 = build(1)
lod2 = build(2)

K.export_asset("HighriseTower103", 1, dict(main=main, lod1=lod1, lod2=lod2, gls=GLS, windows=WS),
               A, K.out_dir_from_argv("output"))
