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
LEDGE_P, LEDGE_T = 0.45, 0.15                 # per-floor ledge projection / thickness (estimated)
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


TEX = {  # tile = one 2.4 m x one storey, so joints line up with floors
    "stone": dict(tile=(2.4, FH), px=256, painter=lambda c: granite(c, 2, 4, 0.3, 7.0)),
    "pale": dict(tile=(2.4, FH), px=256, painter=lambda c: granite(c, 2, 3, 0.12, 2.5)),
    "dark_glass": dict(tile=(1.35, FH), px=128, painter=lambda c: glass_mullions(c)),
    "grey_stone": dict(tile=(2.4, FH), px=256, painter=lambda c: granite(c, 2, 4, 0.18, 4.0)),
    "window": dict(px=1024, painter=window_glass, emissive=(255, 205, 150)),
    "pier_pink": dict(tile=(1.2, 1.2), px=128, painter=lambda c: granite(c, 1, 2, 0.2, 9.0)),
}

A = K.Atlas(size=4096, pad=16)
for name, color, metal, gloss, px in (
        ("stone", (88, 82, 80), 0.0, 0.35, 128),        # dark warm granite (user-02/03/05)
        ("stone_trim", (84, 78, 77), 0.0, 0.35, 64),    # ledges/piers: same stone, untiled (no tile splits)
        ("pale", (224, 222, 214), 0.0, 0.3, 128),       # pale centre panels
        ("crown_white", (232, 233, 230), 0.1, 0.4, 64), # helipad core / rim (user-01)
        ("deck_under", (62, 66, 70), 0.2, 0.35, 64),    # dark helipad underside (user-01)
        ("crown_glass", (96, 150, 140), 0.4, 0.85, 64), # green glazed observatory (user-01, roof.jpg)
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
SIDE_WINS = ((7.4, 10.2, (0.3, 0.7)), (12.0, 14.8, (0.3, 0.7)), (16.4, 20.0, (0.3, 0.7)))
# back (user-01, read as the back elevation): flat bay x < 2 with mixed wide/narrow windows,
# white shaft x 2..5 (no windows), balcony bay x > 5 with wide multi-pane windows
BACK_WINS = ((-15.2, -12.2, (0.3, 0.7)), (-11.4, -7.4, WIDE), (-6.6, -5.4, ()), (-4.4, -0.8, (0.3, 0.7)),
             (5.6, 9.6, (0.3, 0.7)), (10.4, 15.2, WIDE))
# centre panel: user-05 shows windows that change from floor to floor (sizes, pairs)
CENTRE = (
    (((-4.4, -3.0), (-0.7, 0.7), (3.0, 4.4)), SILL),
    (((-4.6, -2.6), (-0.5, 0.5), (2.6, 4.6)), SILL),
    (((-4.4, -3.2), (-1.0, -0.2), (0.2, 1.0), (3.2, 4.4)), 1.1),
)
CENTRE_SEQ = (0, 1, 0, 2, 0, 0, 1, 2, 0, 1, 0, 0, 2)   # fixed irregular order (estimated)


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
    wins, sill = CENTRE[CENTRE_SEQ[f % len(CENTRE_SEQ)]]
    for a0, a1 in wins:
        window(mb, stage, "y", RD, -1, a0, a1, z + sill, z1, f, u); u += 1
    for sgn in (-1, 1):
        for a0, a1, m in SIDE_WINS:
            window(mb, stage, "x", sgn * X, sgn, a0, a1, z0, z1, f, u, m); u += 1
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


def ledges(mb, z, p, t, back="stone_trim"):
    """Ring ledge round the tower except the recess; touching faces skipped (no coplanar pairs)."""
    mb.box(-X - p, -RX, -p, 0, z, z + t, "stone_trim", skip=("back",))
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


def ring(mb, cx, cy, r0, z0, r1, z1, region, n, flip=False):
    """Band of n quads between circle (r0, z0) and circle (r1, z1); normal outward/up unless flip."""
    for i in range(n):
        a, b = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        q = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0), (cx + r0 * math.cos(b), cy + r0 * math.sin(b), z0),
             (cx + r1 * math.cos(b), cy + r1 * math.sin(b), z1), (cx + r1 * math.cos(a), cy + r1 * math.sin(a), z1)]
        mb.rect(q[::-1] if flip else q, region)


# Crown (user-01 crop: round helipad disk on a white core with V struts + green glass observatory;
# research: rooftop helipad and observatory on each tower, top height ~160 m). Sizes estimated.
SHX0, SHX1 = 2.0, 5.0        # back white shaft (user-01); the helipad core rises above it
HX, HY = 3.5, 10.5           # disk centre over the shaft (user-01)
OX0, OX1 = -14.0, -3.0       # observatory x range (other half of the roof, user-01)
HR, HCORE = 8.0, 1.8         # disk / core radius
HZ0 = H + 7.2                # underside meets the core
HZ1 = H + 9.2                # underside meets the rim
HZT = H + 9.8                # deck top (~156.8 m)


def crown(mb, stage):
    n = (32, 24, 12)[stage]
    ring(mb, HX, HY, HCORE, H, HCORE, HZ0, "crown_white", n)                  # core shaft
    ring(mb, HX, HY, HCORE, HZ0, HR, HZ1, "deck_under", n)                    # conical underside (normal points down/out)
    ring(mb, HX, HY, HR, HZ1, HR, HZT, "crown_white", n)                      # rim
    ring(mb, HX, HY, HR, HZT, 0.6, HZT, "deck", n)                            # deck top (centre under the mark)
    mb.box(HX - 5.5, HX + 5.5, HY - 5.5, HY + 5.5, HZT, HZT + 0.03, "heli_green", skip=("bottom",))
    # observatory: green glazed box on the right half (user-01, roof.jpg)
    mb.box(OX0, OX1, 4.0, 17.0, H, H + 5.5, "crown_glass", skip=("bottom",))
    if stage < 2:
        for i in range(6):  # V struts from the core foot to the underside
            a = 2 * math.pi * (i + 0.5) / 6
            r1 = 6.2
            z1 = HZ0 + (HZ1 - HZ0) * (r1 - HCORE) / (HR - HCORE) + 0.1
            prism(mb, (HX + 1.2 * math.cos(a), HY + 1.2 * math.sin(a), H + 1.0),
                  (HX + r1 * math.cos(a), HY + r1 * math.sin(a), z1), 0.45, "crown_white")
        zt = HZT + 0.03
        s = 5.5 / 6.6  # previous mark layout scaled to the 11 m square
        for x0, x1, y0, y1 in ((-6.1, -5.95, -6.1, 6.1), (5.95, 6.1, -6.1, 6.1), (-5.95, 5.95, -6.1, -5.95),
                               (-5.95, 5.95, 5.95, 6.1), (-1.7, -1.4, -2.3, 2.3), (1.4, 1.7, -2.3, 2.3),
                               (-1.4, 1.4, -0.15, 0.15)):
            mb.box(HX + x0 * s, HX + x1 * s, HY + y0 * s, HY + y1 * s, zt, zt + 0.03, "heli_white", skip=("bottom",))
        for i in range(32):
            a, b = 2 * math.pi * i / 32, 2 * math.pi * (i + 1) / 32
            mb.rect([(HX + r * math.cos(t), HY + r * math.sin(t), zt + 0.04)
                     for r, t in ((3.4, a), (3.4, b), (3.28, b), (3.28, a))], "heli_white")
    if stage == 0:
        ring(mb, HX, HY, HR + 0.05, HZT, HR + 0.05, HZT + 0.9, "railing", n)            # safety rail, both faces
        ring(mb, HX, HY, HR + 0.01, HZT, HR + 0.01, HZT + 0.9, "railing", n, flip=True)
        for k in range(1, 8):  # observatory mullions (1.5 m) and transom
            for x in (OX0 + k * (OX1 - OX0) / 8,):
                K.paint(mb, "y", 4.0, -1, x - 0.04, x + 0.04, H, H + 5.5, "frame", layer=2)
                K.paint(mb, "y", 17.0, 1, x - 0.04, x + 0.04, H, H + 5.5, "frame", layer=2)
            y = 4.0 + k * 13.0 / 8
            K.paint(mb, "x", OX0, -1, y - 0.04, y + 0.04, H, H + 5.5, "frame", layer=2)
            K.paint(mb, "x", OX1, 1, y - 0.04, y + 0.04, H, H + 5.5, "frame", layer=2)
        for axis, c, s, a0, a1 in (("y", 4.0, -1, OX0, OX1), ("y", 17.0, 1, OX0, OX1),
                                   ("x", OX0, -1, 4.0, 17.0), ("x", OX1, 1, 4.0, 17.0)):
            K.paint(mb, axis, c, s, a0, a1, H + 2.7, H + 2.8, "frame", layer=3)


def build(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    wing = dict(front="stone", back="pale", left="stone", right="stone", top="roof", bottom="stone")
    # body: wings + recessed centre; centre skips its side faces (inside the wings)
    mb.box(-X, -RX, 0, D, GH, H, dict(wing, right="pale"))
    mb.box(-X, -RX, PIL, D, 0, GH, "stone", skip=("top", "bottom"))
    mb.box(-RX, RX, RD, D, 0, H, dict(front="pale", back="pale", top="roof"), skip=("left", "right", "bottom"))
    mb.box(RX, X, 0, D, 0, H, dict(wing, left="pale"), skip=("bottom",))
    # pale strips on the wings beside the recess, dark stone base on the centre (user-03/05)
    for sgn in (-1, 1):
        K.paint(mb, "y", 0, -1, *sorted((sgn * 9.9, sgn * 7.8)), zf(2), H, "pale")
    K.paint(mb, "y", RD, -1, -RX, RX, 0, zf(2), "stone")
    for sgn in (-1, 1):  # top floors: corner bays turn to dark glass (front + side)
        K.paint(mb, "y", 0, -1, *sorted((sgn * X, sgn * 10.2)), zf(TOPG), H, "dark_glass")
        K.paint(mb, "x", sgn * X, sgn, 0.0, 5.6, zf(TOPG), H, "dark_glass")
    # back (user-01): light grey stone base stepping 6 / 12 floors, grey upper balcony bay, white shaft
    K.paint(mb, "y", D, 1, SHX1, X, 0, zf(6), "grey_stone")
    K.paint(mb, "y", D, 1, -X, SHX0, 0, zf(12), "grey_stone")
    K.paint(mb, "y", D, 1, SHX1, X, zf(30), H, "grey_stone")
    mb.box(SHX0, SHX1, D, D + 0.5, 0, H + 1.3, "white_shaft", skip=("bottom", "front"))
    K.paint(mb, "y", D + 0.5, 1, SHX0, SHX1, 0, zf(4), "grey_stone")
    # pilotis columns under the left wing
    for cx in (-15.5, -10.75, -6.0):
        mb.box(cx - 0.35, cx + 0.35, 0.15, 0.85, 0, GH, "stone_trim", skip=("top", "bottom"))
    if stage < 2:
        for f in range(1, NF + 1):
            if f == 2:
                ledges(mb, zf(f), 0.6, 0.55, "grey_trim")       # podium band
            elif f == NF:
                ledges(mb, H, 0.5, 0.35, "grey_trim")            # cornice
            else:
                ledges(mb, zf(f), LEDGE_P, LEDGE_T, "grey_trim" if f >= 30 else "pale_trim")
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
    # entrance portal (user-03): dark canopy frame, dark left pier, pink granite right pier, stair
    mb.box(7.5, 15.4, -4, -1.6, 4.4, 5.2, "stone_trim")
    mb.box(7.5, 8.5, -4, -3, 0, 4.4, "stone_trim", skip=("bottom", "top"))
    mb.box(14.0, 15.5, -4.4, -2.6, 0, 5.4, "pier_pink", skip=("bottom",))
    if stage < 2:
        mb.box(8.6, 13.9, -1.75, -1.6, 0.6, 4.4, {"front": "glass", "default": "stone_trim"}, skip=("bottom",))
        for i in range(4):
            mb.box(8.6, 13.9, -3.75 + i * 0.5, -3.25 + i * 0.5 if i < 3 else -1.75, 0, 0.15 * (i + 1),
                   "canopy", skip=("bottom", "back"))
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
