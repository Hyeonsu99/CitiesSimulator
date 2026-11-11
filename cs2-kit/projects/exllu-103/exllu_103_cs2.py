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

# ponytail: temporary in-game flicker test switch (set EXLLU_FLICKER_TEST); remove once the cause is known.
#   nomull = no painted mullions/transoms; far = mullions/transoms 7-8 cm out instead of 3-4 cm;
#   winoff = nomull + window quad 6 cm off the wall (5 cm clear of the 1 cm paint layer)
FLICKER_TEST = os.environ.get("EXLLU_FLICKER_TEST", "")
assert FLICKER_TEST in ("", "nomull", "far", "winoff"), FLICKER_TEST
if FLICKER_TEST == "winoff":
    K.WIN_OFF = 0.06

W, D, FH, NF = 32.0, 21.0, 2.94, 50          # TASK: 32 x 21 m, 2.94 m, 50 floors
GH = 5.24                                     # lobby storey: raised so the helipad rail top = 160.0 m (research)
H = GH + FH * (NF - 1)                        # 149.3
REF_F = 26                                    # refuge floor (Naver VR tour band, ~24 rows above / 22 below; +-1, estimated)
TOPG = 41                                     # floors >= TOPG: dark glass corner bays (user-02/05)


def zf(f):
    """Floor level of storey f (0 = lobby)."""
    return 0.0 if f == 0 else GH + (f - 1) * FH

X = W / 2
RX, RD = 1.0, 2.0                             # front slot half-width (user-10: ~2 m wide) / depth (estimated)
PIL = RD                                      # left-wing pilotis back wall flush with the recess (user-03, estimated)
LEDGE_P, LEDGE_T = 0.55, 0.28                 # per-floor ledge projection / thickness (estimated; user-07: ~2x thickness out, ~1/10 storey)
SILL, HEAD = 0.75, 2.45                       # window sill / head above floor (estimated)

def granite(ctx, cols, rows, darken, speck, polish=0.0):
    """Granite cladding: bevelled slab joints, slab-to-slab tone shift, crystal speckle at three scales,
    faint rain streaks and a gloss map (polished slabs, matt joints). Sized for 512-1024 px tiles."""
    k = ctx.w / 256.0
    d = ctx.joints(cols=cols, rows=rows, width_m=0.010, depth=1.4, stagger=0.0, darken=darken, tone=5.0)
    ctx.grain(amp=speck * 0.9, scale_px=max(2, int(1.5 * k)), height=0.5, seed=3)         # crystals
    ctx.rgb += ctx.noise(max(4, int(7 * k)), speck * 0.7, 3, seed=5)[..., None]             # mottling
    ctx.rgb += ctx.noise(max(16, int(40 * k)), speck * 0.5, 2, seed=9)[..., None]           # cloudy patches
    ctx.stains(amount=0.05, scale_px=max(32, int(64 * k)), streaks=0.6, seed=2)
    ctx.gloss[...] = np.clip(ctx.gloss + polish + 0.06 * ctx.noise(max(8, int(20 * k)), 1.0, 2, seed=11), 0.05, 0.95)
    ctx.gloss[d > 0.2] = 0.15


def paving(ctx, n):
    """Honed stone paving / panels: n x n slabs per tile, fine grain, slightly darker joints."""
    ctx.joints(cols=n, rows=n, width_m=0.006, depth=1.0, darken=0.22, tone=3.0)
    ctx.grain(amp=3.0, scale_px=2, height=0.3, seed=4)
    ctx.rgb += ctx.noise(24, 3.0, 2, seed=6)[..., None]


def roofing(ctx):
    """Flat roof membrane: 2 m sheets with lap joints, patchy weathering, puddle stains."""
    ctx.joints(cols=2, rows=2, width_m=0.02, depth=0.6, darken=0.12, tone=3.0)
    ctx.grain(amp=4.0, scale_px=2, height=0.4, seed=7)
    ctx.rgb += ctx.noise(48, 7.0, 3, seed=8)[..., None]
    ctx.stains(amount=0.10, scale_px=96, streaks=0.0, seed=12)


def shutter(ctx):
    """White louvre shutter panel (user-03): frame per 0.6 m leaf, slats every 0.11 m with a shadow line each."""
    mx, mz = ctx.meters()
    sl = (mz / 0.11) % 1.0
    ctx.rgb -= (np.clip(1.0 - sl / 0.22, 0, 1) * 46.0)[..., None]                # shadow under each slat
    ctx.rgb += (np.clip((sl - 0.7) / 0.3, 0, 1) * 8.0)[..., None]                # lit slat edge
    ctx.height += sl * 0.8
    fr = (mx < 0.035) | (mx > ctx.tile[0] - 0.035) | (mz < 0.05) | (mz > ctx.tile[1] - 0.05)
    ctx.rgb[fr] = np.array([236, 237, 234], np.float32)
    ctx.height[fr] = 1.2


def clerestory(ctx):
    """Porch clerestory strip: dark glass panes with a slim white mullion at each tile edge, sky gradient."""
    mx, mz = ctx.meters()
    ctx.rgb += (ctx.v * 26.0 - 6.0)[..., None]
    fr = (mx < 0.025) | (mx > ctx.tile[0] - 0.025) | (mz < 0.03) | (mz > ctx.tile[1] - 0.03)
    ctx.rgb[fr] = np.array([225, 227, 224], np.float32)
    ctx.gloss[...] = np.where(fr, 0.4, 0.9)
    ctx.emis[...] = np.where(fr, 0.0, 0.10)


VEST_W, VEST_H = 5.1, 2.75   # vestibule glazing: clear width between the cheek walls / landing to soffit


def vestibule(ctx):
    """Entrance glazing baked into one texture (no overlay faces): stainless frame, sidelights, a pair of doors
    with pull handles and kick plates, transom lights, dark lobby glass with a warm lit interior at night."""
    x, z = ctx.u * VEST_W, ctx.v * VEST_H
    ctx.rgb[...] = np.array([46, 62, 66], np.float32)
    ctx.rgb += (ctx.v * 34.0)[..., None]                                          # sky reflection
    ctx.rgb += (((x * 0.6 + z) % 1.7 < 0.10) * 16.0)[..., None]                   # glint
    ctx.gloss[...] = 0.9
    ctx.emis[...] = 0.22 + 0.10 * (z < 2.1)
    steel = np.array([172, 176, 178], np.float32)
    fr = (x < 0.07) | (x > VEST_W - 0.07) | (z < 0.06) | (z > VEST_H - 0.07) | (np.abs(z - 2.15) < 0.035)
    for xm in (1.05, VEST_W - 1.05):                                              # sidelight mullions
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
    """Porch soffit: pale panels (one per tile) with a recessed warm downlight at the centre."""
    mx, mz = ctx.meters()
    edge = (mx < 0.012) | (mx > ctx.tile[0] - 0.012) | (mz < 0.012) | (mz > ctx.tile[1] - 0.012)
    ctx.rgb[edge] *= 0.72
    ctx.rgb += ctx.noise(16, 2.0, 2, seed=4)[..., None]
    d = np.hypot(mx - ctx.tile[0] / 2, mz - ctx.tile[1] / 2)
    ctx.emis[...] = np.clip(1.0 - (d / 0.075) ** 4, 0, 1) + 0.22 * np.exp(-(d / 0.35) ** 2)
    ctx.rgb[(d > 0.075) & (d < 0.10)] = np.array([120, 122, 122], np.float32)      # trim ring


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
    h2, h3 = (h * 7) % 1.0, (h * 13) % 1.0
    ctx.rgb[...] = np.array([64, 106, 108], np.float32) + ((h - 0.5) * 18)[..., None]
    ctx.rgb += (fv * 46 - 6)[..., None]                               # sky reflection, brighter towards the top
    m = (fu * 0.7 + fv) % 1.0
    ctx.rgb += (((m > 0.30) & (m < 0.37)) * 20.0)[..., None]          # glint streak
    ctx.rgb += (((m > 0.62) & (m < 0.64)) * 12.0)[..., None]
    edge = np.minimum(np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv))
    ctx.rgb *= (0.72 + 0.28 * np.clip(edge / 0.035, 0, 1))[..., None]  # reveal shadow at the frame
    curt = h2 < 0.45                                                  # side curtains with folds
    cw = 0.10 + 0.08 * h3
    cmask = curt & ((fu < cw) | (fu > 1 - cw))
    fold = 0.82 + 0.18 * np.sin(fu * 90.0 + h * 40.0)
    cloth = np.array([204, 194, 174], np.float32) * fold[..., None]
    ctx.rgb[cmask] = ctx.rgb[cmask] * 0.3 + cloth[cmask] * 0.7
    blind = (~curt) & (h2 > 0.72) & (fv > 0.45 + 0.4 * h3)            # roller blind drawn part-way
    slat = 0.9 + 0.1 * np.sin(fv * 160.0)
    shade = np.array([214, 212, 204], np.float32) * slat[..., None]
    ctx.rgb[blind] = ctx.rgb[blind] * 0.25 + shade[blind] * 0.75
    lit = h3 < 0.3
    level = 0.6 + 0.4 * ((h * 29) % 1.0)                              # rooms are not equally bright
    glow = level * (0.75 + 0.25 * fv) * np.where(cmask | blind, 0.55, 1.0)
    ctx.emis[...] = np.where(lit, glow, 0.0)
    ctx.gloss[...] = np.where(cmask | blind, 0.25, 0.42)


def mesh_grid(ctx, n, w, col):
    """Steel mesh / grating: n x n bar grid of relative width w per tile."""
    m = ((ctx.u * n) % 1.0 < w) | ((ctx.v * n) % 1.0 < w)
    ctx.rgb[m] = np.array(col, np.float32)


def deck_glow(ctx):
    """Grey deck band tile with one perimeter light at its centre: green light pool on the paving at night."""
    mx, mz = ctx.meters()
    d = np.hypot(mx - ctx.tile[0] / 2, mz - ctx.tile[1] / 2)
    ctx.emis[...] = 0.5 * np.exp(-(d / 0.30) ** 2) + 0.10 * np.exp(-(d / 0.75) ** 2)
    ctx.rgb[d < 0.17] = np.array([96, 100, 100], np.float32)          # dark fixture base ring


def flat_emis(v):
    return lambda c: c.emis.__setitem__(Ellipsis, v)


DECK_W = 0.85                # grey deck band between the green pad (12 m) and the deck edge
OBS_GH = 3.65                # observatory glass height between plinth (0.6) and coping (0.35); see observatory()


def obs_glass(ctx):
    """Observatory curtain wall panel (1.2 m x full height): thin frame, transom at 2.6 m, sky reflection brighter
    towards the top, lit interior at night (roof.jpg: the sibling glass crown glows)."""
    mx, mz = ctx.meters()
    ctx.rgb += (ctx.v * 46.0 - 14.0)[..., None]
    fr = (mx < 0.035) | (mx > ctx.tile[0] - 0.035) | (mz < 0.05) | (mz > ctx.tile[1] - 0.05) |          ((mz > 2.58) & (mz < 2.64))
    ctx.rgb[fr] = np.array([210, 214, 212], np.float32)
    ctx.emis[...] = np.where(fr, 0.0, np.where(mz < 2.58, 0.06, 0.03))
    ctx.gloss[...] = np.where(fr, 0.5, 0.92)


def skylight(ctx):
    """Skylight glass: thin grey frame per 1.8 m pane, sky reflection gradient."""
    ctx.rgb += (ctx.v * 30.0 - 8.0)[..., None]
    m = (ctx.u < 0.025) | (ctx.u > 0.975) | (ctx.v < 0.025) | (ctx.v > 0.975)
    ctx.rgb[m] = np.array([150, 156, 160], np.float32)
    ctx.gloss[...] = np.where(m, 0.4, 0.93)


TEX = {  # tile = one 2.4 m x one storey, so joints line up with floors
    "stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 4, 0.3, 7.0, 0.12)),
    "pale": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 3, 0.12, 2.5)),
    "dark_glass": dict(tile=(1.35, FH), px=256, painter=lambda c: glass_mullions(c)),
    "grey_stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 4, 0.18, 4.0)),
    "window": dict(px=2048, painter=window_glass, emissive=(255, 205, 150)),
    "pier_pink": dict(tile=(1.2, 1.2), px=512, painter=lambda c: granite(c, 1, 2, 0.2, 9.0, 0.15)),
    "crown_glass": dict(tile=(1.2, OBS_GH), px=256, painter=lambda c: obs_glass(c), emissive=(255, 228, 185)),
    "obs_roof": dict(tile=(1.8, 1.8), px=256, painter=lambda c: skylight(c)),
    "roof": dict(tile=(4.0, 4.0), px=512, painter=roofing),
    "canopy": dict(tile=(1.2, 1.2), px=256, painter=lambda c: paving(c, 2)),
    "white_shaft": dict(tile=(2.4, FH), px=256, painter=lambda c: paving(c, 2)),
    "louver": dict(tile=(0.6, 2.05), px=256, painter=shutter),
    "clerestory": dict(tile=(0.85, 0.64), px=128, painter=clerestory, emissive=(255, 232, 196)),
    "vestibule": dict(px=1024, painter=vestibule, emissive=(255, 226, 184)),
    "soffit": dict(tile=(1.2, 1.2), px=256, painter=soffit, emissive=(255, 226, 184)),
    "ent_light": dict(px=32, painter=lambda c: c.emis.__setitem__(Ellipsis, 0.8), emissive=(255, 226, 184)),
    "heli_net": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 4, 0.10, (178, 182, 184))),
    "grating": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 12, 0.25, (70, 72, 74))),
    "heli_light": dict(px=32, painter=lambda c: c.emis.__setitem__(Ellipsis, 1.0), emissive=(110, 255, 140)),
    # helideck night lighting (estimated: standard rooftop heliport layout, no night photo of this deck)
    "deck_lit": dict(tile=((2 * 6.85 - DECK_W) / 7, DECK_W), px=128, painter=deck_glow, emissive=(110, 255, 140)),
    "heli_green": dict(px=64, painter=flat_emis(0.07), emissive=(130, 225, 160)),      # floodlit pad
    "heli_white": dict(px=64, painter=flat_emis(0.22), emissive=(255, 250, 236)),      # lit H / border / circle
    "heli_light_y": dict(px=32, painter=flat_emis(1.0), emissive=(255, 214, 90)),      # touchdown circle lights
    "obst_light": dict(px=32, painter=flat_emis(1.0), emissive=(255, 58, 40)),         # red obstruction lights
    "flood_light": dict(px=32, painter=flat_emis(0.8), emissive=(255, 244, 222)),      # deck floodlight lens
    "under_light": dict(px=32, painter=lambda c: c.emis.__setitem__(Ellipsis, 0.15), emissive=(255, 214, 160)),
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
        ("se_glass", (165, 193, 195), 0.5, 0.9, 64),     # SE top glass band, pale blue-grey (user-12; tone estimated)
        ("frame", (236, 237, 235), 0.3, 0.5, 64),       # white window frames
        ("louver", (230, 231, 229), 0.2, 0.4, 64),      # AC louver panels
        ("louver_back", (58, 60, 62), 0.0, 0.3, 64),
        ("roof", (120, 122, 122), 0.0, 0.3, 64),
        ("deck", (150, 152, 150), 0.0, 0.3, 64),
        ("heli_green", (74, 140, 104), 0.0, 0.25, 64),
        ("heli_white", (232, 234, 226), 0.0, 0.25, 64),
        ("pier_pink", (176, 140, 130), 0.0, 0.4, 128),
        ("canopy", (160, 163, 162), 0.2, 0.45, 128),
        ("glass", (150, 185, 180), 0.0, 0.35, 64),      # _Gls pane over every window (green tint, photos)
        ("grey_stone", (168, 168, 164), 0.0, 0.3, 128), # back base + upper bay (user-01)
        ("pale_trim", (226, 224, 218), 0.0, 0.3, 64),  # back ledges, lower floors (user-01)
        ("grey_trim", (150, 151, 148), 0.0, 0.3, 64),  # back ledges, grey upper bay (user-01)
        ("white_shaft", (240, 240, 236), 0.0, 0.3, 64), # back central shaft (user-01)
        ("heli_net", (72, 76, 80), 0.6, 0.4, 64),       # helideck perimeter safety net (steel mesh)
        ("grating", (128, 132, 134), 0.6, 0.35, 64),    # access platform / stair treads
        ("heli_light", (90, 230, 120), 0.0, 0.6, 32),   # green perimeter lights (emissive)
        ("clerestory", (44, 58, 66), 0.5, 0.9, 128),    # porch clerestory panes with baked mullions
        ("vestibule", (46, 62, 66), 0.3, 0.9, 1024),    # entrance doors and sidelights, baked
        ("soffit", (206, 208, 204), 0.0, 0.3, 256),     # porch soffit panels with downlights
        ("ent_light", (250, 240, 220), 0.0, 0.6, 32),   # wall lights on the porch piers
        ("soil", (62, 50, 40), 0.0, 0.1, 64),           # planter top
        ("deck_lit", (150, 152, 150), 0.0, 0.3, 128),   # deck band with a light pool per perimeter light
        ("heli_light_y", (240, 208, 96), 0.0, 0.6, 32), # yellow touchdown circle lights
        ("obst_light", (226, 62, 50), 0.0, 0.6, 32),    # red aviation obstruction lights
        ("flood_light", (246, 244, 234), 0.0, 0.6, 32), # floodlight lens
        ("windsock", (236, 112, 44), 0.0, 0.2, 32),     # orange wind cone
        ("under_light", (250, 236, 210), 0.0, 0.6, 32), # warm downlights under the deck (roof.jpg sibling at night)
        ("window", (70, 110, 110), 0.0, 0.9, 1024)):
    A.add(name, color=color, ctrl=(0, 0, 0), metal=metal, gloss=gloss, **dict(dict(px=px), **TEX.get(name, {})))

WS = K.WindowSet()
GLS = K.MeshBuilder(A)  # glass panes in front of the _Win quads (main only)


def window(mb, stage, axis, c, s, a0, a1, z0, z1, floor, unit, mull=(0.38,), jambs=(True, True)):
    """_Win quad + (main only) projecting white frame, sill and painted mullions/transom.
    jambs=(False, ..) drops the jamb at that end (corner window meeting a corner post).
    On the refuge floor every opening is a louver instead (Naver VR tour: window-less band at mid height)."""
    if floor == REF_F:
        louver(mb, stage, axis, c, s, a0, a1, z0 - 0.35, z1)
        return
    if stage == 0:
        WS.add_face(axis, c, s, a0, a1, z0, z1, floor=floor, unit=unit)
        if jambs[0]:
            K.axbox(mb, axis, c, s, a0 - 0.1, a0, 0, 0.12, z0, z1, "frame", skip=("top", "bottom"))
        if jambs[1]:
            K.axbox(mb, axis, c, s, a1, a1 + 0.1, 0, 0.12, z0, z1, "frame", skip=("top", "bottom"))
        e0, e1 = (0.1 if jambs[0] else 0.0), (0.1 if jambs[1] else 0.0)
        K.axbox(mb, axis, c, s, a0 - e0, a1 + e1, 0, 0.12, z1, z1 + 0.1, "frame")
        K.axbox(mb, axis, c, s, a0 - (0.15 if jambs[0] else 0.0), a1 + (0.15 if jambs[1] else 0.0),
                0, 0.18, z0 - 0.1, z0, "frame")
        if FLICKER_TEST in ("nomull", "winoff"):
            return
        lm = 7 if FLICKER_TEST == "far" else 3
        for u in mull:  # never at u=0.5 so the window centre stays unblocked
            a = a0 + (a1 - a0) * u
            K.paint(mb, axis, c, s, a - 0.03, a + 0.03, z0, z1, "frame", layer=lm)
        zt = z0 + 0.55 * (z1 - z0)
        K.paint(mb, axis, c, s, a0, a1, zt, zt + 0.05, "frame", layer=lm + 1)


def louver(mb, stage, axis, c, s, a0, a1, z0, z1):
    if stage == 0:
        K.axbox(mb, axis, c, s, a0, a1, 0, 0.08, z0, z1, "louver")   # slats baked into the texture


WIDE = (0.1, 0.4, 0.46, 0.54, 0.6, 0.9)   # two sash units (narrow + wide each), paired mullion at the joint (user-03/11)
PAIR = (0.18, 0.46, 0.54, 0.82)          # shorter windows: narrow, wide | wide, narrow
BAYW = 0.4                   # right-wing bay window projection (estimated)
TZ = 1.05                    # raised terrace / lobby floor level = porch landing (7 x 0.15 m)
CW = 0.15                    # corner window stops this far from the wall corner; a post fills the gap
SIDE_WINS = ((7.4, 10.2, PAIR), (12.0, 14.8, PAIR), (16.4, 20.0, PAIR))  # lobby floor only
# SE side (-x), user-12-se (close, frontal; same face as user-07/08): dark stone flanks ~3 m at both ends full height
# with a ledge every floor, pale centre above PALE_F, teal glass band on the top 4 floors, regular windows each floor
# (positions read along one row of user-12, estimated); no corner window wraps onto this side
SIDE_PALE = (3.0, 18.0)
PALE_F = 7                   # user-07: side centre is dark stone with full-width ledges below this floor (estimated count)
SIDE_LOUVER = (10.1, 12.0)   # white shutter column
SE_WINS = ((0.6, 2.2, (0.38,)), (3.6, 6.2, PAIR), (7.3, 8.1, ()), (8.4, 9.8, (0.38,)), (12.3, 13.2, ()),
           (14.3, 16.8, PAIR), (18.2, 20.4, (0.38,)))
SE_GLASS = (4.8, 13.4)       # top glass band (user-12)
# NW side (+x), Naver street view 2025-03 (pano adGlg.., ~47 m WNW): pale above PALE_F with no side ledges,
# full-height dark slot ~9 m from the front corner, pairs of small windows either side of it, wide windows outside
SL0, SL1, SLD = 8.8, 10.4, 1.2   # slot y range / depth (estimated from the panorama)
NW_WINS = ((6.6, 7.4, 1.1, ()), (7.8, 8.5, 1.1, ()), (10.7, 11.4, 1.1, ()), (11.8, 12.5, 1.1, ()),
           (13.0, 15.6, SILL, PAIR), (16.4, 20.2, SILL, WIDE))
# back (user-01, read as the back elevation): flat bay x < 2 with mixed wide/narrow windows,
# white shaft x 2..5 (no windows), balcony bay x > 5 with wide multi-pane windows
BACK_WINS = ((-15.2, -12.2, PAIR), (-11.4, -7.4, WIDE), (-6.6, -5.4, ()), (-4.4, -0.8, PAIR),
             (5.6, 9.6, PAIR), (10.4, 15.2, WIDE))


def corner_bay(mb, stage, sgn, z, f, u, front=True):
    """Front corner of a wing: one window wrapping round the corner (user-04), dark glass on top floors (user-02/05)."""
    top = f >= TOPG
    z0, z1 = (z + 0.3, z + FH - 0.3) if top else (z + SILL, z + HEAD)
    mull = WIDE if not top else (0.12, 0.26, 0.4, 0.6, 0.74, 0.88)
    # front face: corner end is the outer end (a1 for the right wing, a0 for the left)
    a0, a1 = (-(X - CW), -10.4) if sgn < 0 else (10.4, X - CW)
    if front:
        window(mb, stage, "y", 0, -1, a0, a1, z0, z1, f, u, mull,
               jambs=(sgn > 0, sgn < 0))
    # side face: a = y, corner end is a0 (y = 0)
    if sgn > 0:   # the wrap is on the NW corner only (user-04); the SE side has its own flank window (user-12)
        window(mb, stage, "x", sgn * X, sgn, CW, 5.4, z0, z1, f, u + 1, PAIR if not top else (0.25, 0.75),
               jambs=(False, True))
    if stage == 0 and front:
        K.corner_post(mb, sgn * X, 0.0, sgn, -1, 0.12, z0, z1, "frame")
    return u + 2


def floor_facade(mb, stage, f):
    """Windows and louvers of one upper floor f (f >= 1)."""
    z = zf(f)
    z0, z1, u = z + SILL, z + HEAD, 0
    for sgn in (-1, 1):  # front wings, mirrored
        a = lambda p, q: (min(sgn * p, sgn * q), max(sgn * p, sgn * q))
        band = f == 1 and sgn < 0           # user-03: floor 1 of the left wing is a solid stone band over the pilotis
        u = corner_bay(mb, stage, sgn, z, f, u, front=not band)
        if not band:
            # user-10: corner window, window, white louver, small window, then the slot
            window(mb, stage, "y", 0, -1, *a(6.6, 9.2), z0, z1, f, u, PAIR); u += 1
            louver(mb, stage, "y", 0, -1, *a(3.2, 4.4), z + 0.4, z1)
            if sgn > 0:   # right wing: small bay window with glazed returns (user-03)
                if stage == 0:
                    mb.box(1.3, 2.7, -BAYW, 0, z0 - 0.1, z1 + 0.1, dict(left="glass", right="glass", default="frame"),
                           skip=("back",))
                window(mb, stage, "y", -BAYW, -1, 1.4, 2.6, z0, z1, f, u); u += 1
            else:
                window(mb, stage, "y", 0, -1, -2.6, -1.4, z0, z1, f, u); u += 1
        # slot side wall (left wing faces +x, right wing faces -x)
        window(mb, stage, "x", sgn * RX, -sgn, 0.6, 1.5, z0, z1, f, u); u += 1
    window(mb, stage, "y", RD, -1, -0.55, 0.55, z0, z1, f, u); u += 1   # slot back wall: one small window per floor (user-03)
    for a0, a1, m in SE_WINS:                                # SE side (user-12)
        window(mb, stage, "x", -X, -1, a0, a1, z0, z1, f, u, m); u += 1
    louver(mb, stage, "x", -X, -1, *SIDE_LOUVER, z + 0.4, z1)
    for a0, a1, sl, m in NW_WINS:                            # NW side (street view)
        window(mb, stage, "x", X, 1, a0, a1, z + sl, z1, f, u, m); u += 1
    for a0, a1, m in BACK_WINS:
        window(mb, stage, "y", D, 1, a0, a1, z0, z1, f, u, m); u += 1


def ground_floor(mb, stage):
    z0, z1, u = 0.3, GH - 0.6, 0          # double-height lobby glazing
    zs0, zs1 = SILL, GH - 0.8
    window(mb, stage, "y", 0, -1, 14.2, 15.4, z0, z1, 0, u); u += 1
    # left wing pilotis stay open (user-03: bicycle parking, no glazing); slot: door off the raised terrace
    window(mb, stage, "y", RD, -1, -0.6, 0.6, TZ + 0.05, TZ + 2.3, 0, u); u += 1
    window(mb, stage, "x", X, 1, 1.0, 5.4, zs0, zs1, 0, u, PAIR); u += 1   # right side front bay
    for sgn in (-1, 1):
        for a0, a1, m in SIDE_WINS:
            window(mb, stage, "x", sgn * X, sgn, a0, a1, zs0, zs1, 0, u, m); u += 1
    for a0, a1, m in BACK_WINS:
        window(mb, stage, "y", D, 1, a0, a1, zs0, zs1, 0, u, m); u += 1


def ledges(mb, z, p, t, back="stone_trim", side_gap=False):
    """Ring ledge round the tower except the recess; touching faces skipped (no coplanar pairs).
    side_gap: the side ledges stop at the pale side centre (user-07: flanks only above PALE_F)."""
    front = "pale_trim" if side_gap else "stone_trim"  # estimated: pale upper storey bands, user-11
    mb.box(-X - p, -RX, -p, 0, z, z + t, front, skip=("back",))
    if side_gap:   # SE: flanks only; NW: no side ledge (street view); front ledge ends in a corner piece; no back ledge
        mb.box(RX, X, -p, 0, z, z + t, front, skip=("back", "right"))
        mb.box(X, X + p, -p, 0, z, z + t, front, skip=("left",))
        for y0, y1, ends in ((0, SIDE_PALE[0], ("front",)), (SIDE_PALE[1], D, ())):
            mb.box(-X - p, -X, y0, y1, z, z + t, "stone_trim", skip=ends + ("right",))
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
        heli_lights(mb, stage)


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


def heli_lights(mb, stage):
    """Helideck night lighting (estimated standard layout): green perimeter lights with light pools painted on
    the deck band (pinwheel of four strips, 7 lights each), yellow touchdown-circle lights, rail-top floodlights
    facing the pad, red obstruction lights on the deck corners, lit windsock on the NE net corner."""
    w, z = DECK_W, HZT + 0.03                       # band flush with the green pad top
    L = 2 * HS - w
    T = L / 7
    x0, x1, y0, y1 = HX - HS, HX + HS, HY - HS, HY + HS
    strips = (((x0, y0), (1, 0), (0, 1)), ((x1, y0), (0, 1), (-1, 0)),      # origin, along, across
              ((x1, y1), (-1, 0), (0, -1)), ((x0, y1), (0, -1), (1, 0)))
    for (ox, oy), (ax, ay), (cx, cy) in strips:
        mb.rect([(ox, oy, z), (ox + ax * L, oy + ay * L, z),
                 (ox + ax * L + cx * w, oy + ay * L + cy * w, z), (ox + cx * w, oy + cy * w, z)], "deck_lit")
        if stage == 0:
            for i in range(7):
                x = ox + ax * (i + 0.5) * T + cx * w / 2
                y = oy + ay * (i + 0.5) * T + cy * w / 2
                mb.box(x - 0.09, x + 0.09, y - 0.09, y + 0.09, z, z + 0.09, "heli_light", skip=("bottom",))
    if stage > 0:
        return
    for i in range(16):                             # touchdown circle lights on the white ring
        a = 2 * math.pi * (i + 0.5) / 16
        x, y = HX + 3.64 * math.cos(a), HY + 3.64 * math.sin(a)
        mb.box(x - 0.07, x + 0.07, y - 0.07, y + 0.07, HZT + 0.07, HZT + 0.13, "heli_light_y", skip=("bottom",))
    zr = HZT + 0.9                                  # rail top
    body = dict(default="railing", top="railing")
    for t in (-3.2, 3.2):                           # floodlights on the rail, lens towards the pad
        mb.box(HX + t - 0.3, HX + t + 0.3, y0 - 0.14, y0 + 0.06, zr, zr + 0.2, dict(body, back="flood_light"), skip=("bottom",))
        mb.box(HX + t - 0.3, HX + t + 0.3, y1 - 0.06, y1 + 0.14, zr, zr + 0.2, dict(body, front="flood_light"), skip=("bottom",))
        mb.box(x0 - 0.14, x0 + 0.06, HY + t - 0.3, HY + t + 0.3, zr, zr + 0.2, dict(body, right="flood_light"), skip=("bottom",))
        mb.box(x1 - 0.06, x1 + 0.14, HY + t - 0.3, HY + t + 0.3, zr, zr + 0.2, dict(body, left="flood_light"), skip=("bottom",))
    for sx in (-1, 1):                              # red obstruction lights on the deck rail corners
        for sy in (-1, 1):
            x, y = HX + sx * (HS + 0.03), HY + sy * (HS + 0.03)
            mb.box(x - 0.1, x + 0.1, y - 0.1, y + 0.1, zr, zr + 0.22, "obst_light", skip=("bottom",))
    mx, my, zn = x1 + NET - 0.3, y0 - NET + 0.3, HZT - 0.02      # windsock mast on the NE net corner
    mb.box(mx - 0.05, mx + 0.05, my - 0.05, my + 0.05, zn, zn + 3.2, "crown_white", skip=("bottom", "top"))
    mb.box(mx - 0.09, mx + 0.09, my - 0.09, my + 0.09, zn + 3.2, zn + 3.4, "obst_light", skip=("bottom",))
    mb.box(mx + 0.05, mx + 0.95, my - 0.17, my + 0.17, zn + 2.6, zn + 2.94, "windsock", skip=("left",))
    mb.box(mx + 0.95, mx + 1.5, my - 0.11, my + 0.11, zn + 2.66, zn + 2.88, "windsock", skip=("left",))


def heli_access(mb):
    """Switchback steel access stair from the main roof to the SE platform."""
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
    raised stair between stone cheek walls with steel handrails and open right portico; recessed dark glass vestibule.
    The "103" numerals and the sign lettering are not modeled (no sign text)."""
    mb.box(7.5, 15.55, EY, 0, EZ0, EZT, dict(front="pale", right="pale", left="stone", top="roof",
                                             bottom="soffit"), skip=("back",))
    mb.box(7.4, 8.6, EY - 0.1, EY + 1.1, 0, EZT + 0.1, "stone_trim", skip=("bottom",))         # left pier
    mb.box(13.7, 15.7, EY - 0.2, EY + 1.8, 0, EZT + 0.3,
           dict(front="pier_pink", right="stone", left="stone_trim", top="stone_trim", default="pier_pink"),
           skip=("bottom",))                                                                  # corner pier
    if stage == 2:
        return
    for axis, c, s, a0, a1 in (("y", EY, -1, 8.6, 13.7), ("x", 15.55, 1, EY + 1.8, 0.0)):
        K.paint(mb, axis, c, s, a0, a1, EZC, EZT, "stone", layer=2)                           # cap band
        K.paint(mb, axis, c, s, a0 + 0.2, a1 - 0.2, EZB + 0.08, EZC - 0.08, "clerestory", layer=2)  # clerestory
        K.paint(mb, axis, c, s, a0, a1, EZB, EZB + 0.08, "frame", layer=3)
    yl = EY + ST_N * ST_T                                                                     # landing front
    for i in range(ST_N):                                                                     # steps
        y0 = EY + i * ST_T
        mb.box(8.6, 13.7, y0, y0 + ST_T, 0, ST_R * (i + 1), "canopy",
               skip=("bottom", "back", "left", "right"))
    zl = ST_N * ST_R
    mb.box(8.6, 13.7, yl, 0, 0, zl, "canopy", skip=("bottom", "back", "left", "right"))     # landing extends to tower
    mb.box(8.6, 13.7, -0.05, 0.0, zl, EZ0, {"front": "vestibule", "default": "stone_trim"},
           skip=("bottom", "top", "back", "left", "right"))                                  # entrance doors at facade
    for x0, x1, y0 in ((8.2, 8.6, EY + 1.1), (13.7, 14.1, EY + 1.8)):                         # cheek walls
        mb.box(x0, x1, y0, 0, 0, zl + 0.2, "stone_trim", skip=("bottom", "front", "back"))  # cheek walls to tower
    if stage == 0:
        ya = EY + 0.2
        rail_z = lambda y: ST_R + (y - ya) / (yl - ya) * (zl - ST_R)                           # stair pitch line
        for x in (8.75, 11.15):                                                               # left & center handrails
            for dz in (0.9, 0.45):
                prism(mb, (x, ya, dz + rail_z(ya)), (x, yl, dz + rail_z(yl)), 0.05, "railing")
            for k in range(4):
                yy = ya + k * (yl - ya - 0.1) / 3
                zb = ST_R * min(ST_N, 1 + int((yy - EY) / ST_T))                              # tread under the post
                mb.box(x - 0.03, x + 0.03, yy - 0.03, yy + 0.03, zb, 0.9 + rail_z(yy), "railing", skip=("bottom",))
        # right side safety railing: multi-bar railing along stair and landing to tower (user photo: open with railing)
        xr = 13.66
        for dz in (0.90, 0.72, 0.54, 0.36, 0.18):
            prism(mb, (xr, ya, dz + rail_z(ya)), (xr, yl, dz + rail_z(yl)), 0.04 if dz < 0.9 else 0.05, "railing")
            prism(mb, (xr, yl, dz + zl), (xr, 0.0, dz + zl), 0.04 if dz < 0.9 else 0.05, "railing")
        for k in range(4):
            yy = ya + k * (yl - ya - 0.1) / 3
            zb = ST_R * min(ST_N, 1 + int((yy - EY) / ST_T))
            mb.box(xr - 0.03, xr + 0.03, yy - 0.025, yy + 0.025, zb, 0.9 + rail_z(yy), "railing", skip=("bottom",))
        for yy in (yl, (yl + 0.0) / 2, 0.0):                                                  # landing posts
            mb.box(xr - 0.03, xr + 0.03, yy - 0.025, yy + 0.025, zl, zl + 0.9, "railing", skip=("bottom",))


def terrace(mb, stage):
    """Raised stone terrace in front of the slot, level with the porch landing, steel rails on the open edges
    (user-03: rails left of the slot and beside the porch; extent estimated)."""
    mb.box(-4.0, 5.8, -2.0, 0, 0, TZ, dict(top="canopy", default="stone_trim"), skip=("back", "bottom"))
    mb.box(-4.0, RX, 0, RD, 0, TZ, dict(top="canopy", default="stone_trim"),
           skip=("front", "back", "right", "bottom"))
    if stage:
        return
    for p0, p1 in (((-3.92, -1.92), (5.72, -1.92)), ((-3.92, -1.92), (-3.92, 1.9))):
        for dz in (0.45, 0.9):
            prism(mb, (p0[0], p0[1], TZ + dz), (p1[0], p1[1], TZ + dz), 0.05, "railing")
    for x, y in [(-3.92 + i * 1.6, -1.92) for i in range(7)] + [(-3.92, 0.0), (-3.92, 1.9)]:
        mb.box(x - 0.03, x + 0.03, y - 0.03, y + 0.03, TZ, TZ + 0.92, "railing", skip=("bottom",))


def entrance_extras(mb):
    """Warm wall lights on the two porch piers and a low granite planter beside the stair (main LOD only)."""
    # on the pier faces towards the stair: a lamp on the pier fronts would push the lot depth past 26 m (5x5)
    mb.box(8.6, 8.66, EY + 0.3, EY + 0.6, 2.4, 2.75, "ent_light", skip=("left",))
    mb.box(13.64, 13.7, EY + 0.3, EY + 0.6, 2.4, 2.75, "ent_light", skip=("right",))
    mb.box(5.95, 7.25, -3.9, -2.6, 0, 0.6, dict(top="soil", default="stone_trim"), skip=("bottom",))


def build(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    wing = dict(front="stone", back="pale", left="stone", right="stone", top="roof", bottom="stone")
    # body: wings + recessed centre; centre skips its side faces (inside the wings)
    mb.box(-X, -RX, 0, D, GH, H, wing)
    mb.box(-X, -RX, PIL, D, 0, GH, "stone", skip=("top", "bottom"))
    mb.box(-RX, RX, RD, D, 0, H, dict(front="stone", back="pale", top="roof"), skip=("left", "right", "bottom"))
    # right wing split round the NW full-height slot (street view): slot walls dark stone, slot back darker
    rw = wing
    mb.box(RX, X, 0, SL0, 0, H, dict(rw, back="stone"), skip=("bottom",))
    mb.box(RX, X, SL1, D, 0, H, dict(rw, front="stone"), skip=("bottom",))
    mb.box(RX, X, SL0, SL1, 0, GH, rw, skip=("bottom", "front", "back", "left"))
    mb.box(RX, X - SLD, SL0, SL1, GH, H, dict(rw, right="louver_back"), skip=("bottom", "front", "back", "left"))
    # user-10 / sv-front: front wings dark stone up to PALE_F, pale above; the narrow slot stays dark stone
    for sgn in (-1, 1):
        K.paint(mb, "y", 0, -1, *sorted((sgn * 10.2, sgn * 3.0)), zf(PALE_F), H, "pale")   # user-11: dark stone strips |x| < 3 beside the slot, full height
        K.paint(mb, "y", 0, -1, *sorted((sgn * X, sgn * 10.2)), zf(PALE_F), zf(TOPG), "pale")   # dark glass above
    for sgn in (-1, 1):  # top floors: corner bays turn to dark glass (front + side)
        K.paint(mb, "y", 0, -1, *sorted((sgn * X, sgn * 10.2)), zf(TOPG), H, "dark_glass")
    K.paint(mb, "x", -X, -1, *SIDE_PALE, zf(PALE_F), zf(NF - 4), "pale")      # SE side (user-12)
    K.paint(mb, "x", -X, -1, SIDE_PALE[0], SE_GLASS[0], zf(NF - 4), H, "pale")
    K.paint(mb, "x", -X, -1, *SE_GLASS, zf(NF - 4), H, "se_glass")
    K.paint(mb, "x", -X, -1, SE_GLASS[1], SIDE_PALE[1], zf(NF - 4), H, "pale")
    for a0, a1 in ((0.0, SL0), (SL1, D)):                                      # NW side all pale (street view)
        K.paint(mb, "x", X, 1, a0, a1, zf(PALE_F), H, "pale")
    # back (user-01): light grey stone base stepping 6 / 12 floors, grey upper balcony bay, white shaft
    # street view (2025-03, SSW): the back base is the same dark granite as the sides, up to PALE_F
    K.paint(mb, "y", D, 1, SHX1, X, 0, zf(PALE_F), "stone")
    K.paint(mb, "y", D, 1, -X, SHX0, 0, zf(PALE_F), "stone")
    # back above PALE_F: SE half (x < shaft) grey, NW half pale, no ledges (Kakao roadview 2023-02 overcast, 81 m SSW;
    # the 2025-09 sunny view washes the grey out; matches the Naver street view 2025-03 from the south)
    K.paint(mb, "y", D, 1, -X, SHX0, zf(PALE_F), H, "grey_stone")
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
    if stage == 0:                                  # red obstruction lights on the roof parapet corners (estimated)
        for sx in (-1, 1):
            for sy, yc in ((-1, 0.15), (1, D - 0.15)):
                xc = sx * (X - 0.15)
                mb.box(xc - 0.12, xc + 0.12, yc - 0.12, yc + 0.12, PH, PH + 0.25, "obst_light", skip=("bottom",))
    crown(mb, stage)
    entrance(mb, stage)
    if stage == 0:
        entrance_extras(mb)
    if stage < 2:
        terrace(mb, stage)
        # floor 1 of the left wing: solid grey granite band over the pilotis (user-03); ledges cap top and bottom
        mb.box(-X, -RX, -0.3, 0, zf(1) + LEDGE_T, zf(2), "grey_stone", skip=("back", "top", "bottom"))
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
