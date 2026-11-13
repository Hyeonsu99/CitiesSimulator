"""Tower 103: 50-floor stepped Type-A tower (OSM way 934368144) with SE curtain crown & openwork helipad.

Custom generator (replaces the generic-spec version kept in work/exllu_103_cs2.v1_generic.py).
Evidence: OSM way 934368144 + photos/* (see work/observations.json). Dimensions not in TASK are estimated.
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

# No _Gls glass mesh: the pane in front of the _Win quads flickered at night in game (user test 2026-11-11).

D, FH, NF = 23.80, 2.94, 50                    # OSM way 934368144 depth (23.8 m), 2.94 m storey, 50 floors
GH = 5.24                                       # lobby storey: raised so the helipad rail top ~ 160 m
H = GH + FH * (NF - 1)                          # 149.30
REF_F = 26                                      # refuge floor (Naver VR tour band at mid height)
PALE_F = 7                                      # dark granite podium floors 0..6, pale upper 7..49

# Canonical OSM footprint (way 934368144 rotated so NE entrance faces -Y, -X = SE glass, +X = NW helipad):
# width X in [-13.70, +13.60] = 27.30 m, depth Y in [0.00, 23.80] = 23.80 m.
SE_X, SE_XOUT, SE_Y0, SE_Y1 = -12.00, -13.70, 3.55, 20.05
NW_X, NW_NIN, NW_Y0, NW_Y1 = 13.60, 12.05, 8.85, 13.55
FS_X0, FS_X1, FS_D = -2.50, 0.40, 1.15          # front (NE) vertical slot (2.90 x 1.15 m)
BS_X0, BS_X1, BS_D = -2.65, 0.15, 1.10          # back (SW) vertical slot (2.80 x 1.10 m)
PIL_D = 1.90                                    # left-wing ground pilotis inset depth (user-03)
LEDGE_P, LEDGE_T = 0.55, 0.28                   # per-floor ledge projection / thickness
SILL, HEAD = 0.75, 2.45                         # window sill / head above floor

# Exact 20-vertex CCW plan outline (edge outward normals point strictly exterior)
OUTLINE = [
    (SE_X, 0.00), (FS_X0, 0.00), (FS_X0, FS_D), (FS_X1, FS_D), (FS_X1, 0.00),
    (NW_X, 0.00), (NW_X, NW_Y0), (NW_NIN, NW_Y0), (NW_NIN, NW_Y1), (NW_X, NW_Y1),
    (NW_X, D), (BS_X1, D), (BS_X1, D - BS_D), (BS_X0, D - BS_D), (BS_X0, D),
    (SE_X, D), (SE_X, SE_Y1), (SE_XOUT, SE_Y1), (SE_XOUT, SE_Y0), (SE_X, SE_Y0),
]

# Exact disjoint rectangle decomposition of OUTLINE for roof & flat soffit/stage-2 fills
ROOF_RECTS = [
    (SE_XOUT, SE_X, SE_Y0, SE_Y1),
    (SE_X, BS_X0, 0.00, D),
    (BS_X0, FS_X0, 0.00, D - BS_D),
    (FS_X0, BS_X1, FS_D, D - BS_D),
    (BS_X1, FS_X1, FS_D, D),
    (FS_X1, NW_NIN, 0.00, D),
    (NW_NIN, NW_X, 0.00, NW_Y0),
    (NW_NIN, NW_X, NW_Y1, D),
]


def zf(f):
    """Floor level of storey f (0 = lobby)."""
    return 0.0 if f == 0 else GH + (f - 1) * FH

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
    ctx.emis[...] = np.where(fr, 0.0, 0.04)


VEST_W, VEST_H = 5.1, 2.75   # vestibule glazing: clear width between the cheek walls / landing to soffit


def vestibule(ctx):
    """Entrance glazing baked into one texture (no overlay faces): stainless frame, sidelights, a pair of doors
    with pull handles and kick plates, transom lights, dark lobby glass with a warm lit interior at night."""
    x, z = ctx.u * VEST_W, ctx.v * VEST_H
    ctx.rgb[...] = np.array([46, 62, 66], np.float32)
    ctx.rgb += (ctx.v * 34.0)[..., None]                                          # sky reflection
    ctx.rgb += (((x * 0.6 + z) % 1.7 < 0.10) * 16.0)[..., None]                   # glint
    ctx.gloss[...] = 0.9
    ctx.emis[...] = 0.07 + 0.03 * (z < 2.1)       # entrance emissive cut to ~1/3 (too bright in game, 2026-11-11)
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
    ctx.emis[...] = 0.35 * np.clip(1.0 - (d / 0.075) ** 4, 0, 1) + 0.05 * np.exp(-(d / 0.35) ** 2)
    ctx.rgb[(d > 0.075) & (d < 0.10)] = np.array([120, 122, 122], np.float32)      # trim ring


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
    # Lit rooms are whole grid cells (LIT_CELLS of 25, one contiguous block), not scattered slots: slots are only
    # ~50 px, so at distant mip levels every lit slot bled into its dark neighbours and showed as rows of warm
    # dots on the facade (user screenshots 2026-11-11). window() spreads the windows over the cells at random.
    lit = (np.floor(ctx.v * g).astype(np.int64) * g + np.floor(ctx.u * g).astype(np.int64)) < LIT_CELLS
    r = max(1, round(ctx.w * 0.008))                                  # 16 px unlit guard along the block's edge
    m = np.pad(lit, r, constant_values=True)
    for ax in (0, 1):
        m = np.logical_and.reduce([np.roll(m, k, ax) for k in range(-r, r + 1)])
    lit = m[r:-r, r:-r]
    level = 0.6 + 0.4 * ((h * 29) % 1.0)                              # rooms are not equally bright
    glow = level * (0.75 + 0.25 * fv) * np.where(cmask | blind, 0.55, 1.0)
    ctx.emis[...] = np.where(lit, glow, 0.0)
    ctx.gloss[...] = np.where(cmask | blind, 0.25, 0.42)


def mesh_grid(ctx, n, w, col, alpha_cut=False):
    """Steel mesh / grating: n x n bar grid of relative width w per tile; optional alpha-cut holes."""
    m = ((ctx.u * n) % 1.0 < w) | ((ctx.v * n) % 1.0 < w)
    ctx.rgb[m] = np.array(col, np.float32)
    if alpha_cut:
        ctx.alpha[...] = np.where(m, 255.0, 0.0)


def deck_glow(ctx):
    """Grey deck band tile with the dark base ring of one perimeter light at its centre (no painted light pool)."""
    mx, mz = ctx.meters()
    d = np.hypot(mx - ctx.tile[0] / 2, mz - ctx.tile[1] / 2)
    ctx.rgb[d < 0.17] = np.array([96, 100, 100], np.float32)          # dark fixture base ring


def flat_emis(v):
    return lambda c: c.emis.__setitem__(Ellipsis, v)


HS = 7.4                     # helipad deck half-size (14.8 x 14.8 m, aerial user-09 / site.jpg)
DECK_W = 0.85                # grey deck band between the green pad and the deck edge
OBS_GH = 3.95                # observatory glass height between plinth (0.65) and coping (0.40)


def obs_glass(ctx):
    """Observatory curtain wall panel (1.2 m x full height): slim aluminum frame, transom at 2.6 m,
    sky reflection, strong warm-green interior night glow (roof.jpg)."""
    mx, mz = ctx.meters()
    ctx.rgb += (ctx.v * 44.0 - 12.0)[..., None]
    fr = (mx < 0.032) | (mx > ctx.tile[0] - 0.032) | (mz < 0.05) | (mz > ctx.tile[1] - 0.05) | ((mz > 2.58) & (mz < 2.64))
    ctx.rgb[fr] = np.array([208, 212, 210], np.float32)
    glow = 0.42 * (1.0 - 0.55 * np.clip(mz / OBS_GH, 0.0, 1.0)) + 0.14
    ctx.emis[...] = np.where(fr, 0.0, glow)
    ctx.gloss[...] = np.where(fr, 0.5, 0.92)


def se_curtain(ctx):
    """SE top 4-floor glazed curtain wall (user-12-se / site.jpg): slim mullions, dark slab spandrel band,
    sky-blue-teal glass gradient, soft warm night interior glow."""
    mx, mz = ctx.meters()
    ctx.rgb += (ctx.v * 34.0 - 10.0)[..., None]
    spandrel = (mz < 0.42) | (mz > ctx.tile[1] - 0.12)
    ctx.rgb[spandrel] = np.array([62, 78, 86], np.float32)
    mull = (mx < 0.030) | (mx > ctx.tile[0] - 0.030)
    trans = (mz >= 0.42) & (mz < 0.48)
    fr = mull | trans | ((mz > 1.72) & (mz < 1.76))
    ctx.rgb[fr] = np.array([210, 214, 216], np.float32)
    ctx.emis[...] = np.where(fr | spandrel, 0.0, 0.18)
    ctx.gloss[...] = np.where(fr, 0.48, np.where(spandrel, 0.55, 0.93))


def skylight(ctx):
    """Skylight glass: thin grey frame per 1.8 m pane, sky reflection gradient."""
    ctx.rgb += (ctx.v * 30.0 - 8.0)[..., None]
    m = (ctx.u < 0.025) | (ctx.u > 0.975) | (ctx.v < 0.025) | (ctx.v > 0.975)
    ctx.rgb[m] = np.array([150, 156, 160], np.float32)
    ctx.gloss[...] = np.where(m, 0.4, 0.93)


def foliage_tex(ctx):
    """Shrubbery foliage: deep evergreen base with leafy mottling."""
    ctx.grain(amp=12.0, scale_px=2, height=0.6, seed=21)
    ctx.rgb += ctx.noise(16, 10.0, 2, seed=23)[..., None]


TEX = {  # tile = one 2.4 m x one storey, so joints line up with floors
    "foliage": dict(tile=(1.2, 1.2), px=64, painter=foliage_tex),
    "stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 4, 0.25, 6.5, 0.12)),
    "pale": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 3, 0.08, 2.2)),
    "grey_stone": dict(tile=(2.4, FH), px=1024, painter=lambda c: granite(c, 2, 4, 0.15, 3.8)),
    "window": dict(px=2048, painter=window_glass, emissive=(255, 205, 150)),
    "pier_pink": dict(tile=(1.2, 1.2), px=512, painter=lambda c: granite(c, 1, 2, 0.18, 8.0, 0.15)),
    "crown_glass": dict(tile=(1.2, OBS_GH), px=256, painter=obs_glass, emissive=(225, 250, 185)),
    "se_glass": dict(tile=(9.10 / 8, FH), px=512, painter=se_curtain, emissive=(255, 224, 175)),
    "obs_roof": dict(tile=(1.8, 1.8), px=256, painter=skylight),
    "roof": dict(tile=(4.0, 4.0), px=512, painter=roofing),
    "canopy": dict(tile=(1.2, 1.2), px=256, painter=lambda c: paving(c, 2)),
    "louver": dict(tile=(0.6, 2.05), px=256, painter=shutter),
    "clerestory": dict(tile=(0.85, 0.64), px=128, painter=clerestory, emissive=(255, 232, 196)),
    "vestibule": dict(px=1024, painter=vestibule, emissive=(255, 226, 184)),
    "soffit": dict(tile=(1.2, 1.2), px=256, painter=soffit, emissive=(255, 226, 184)),
    "ent_light": dict(px=32, painter=lambda c: c.emis.__setitem__(Ellipsis, 0.25), emissive=(255, 226, 184)),
    "heli_net": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 3, 0.22, (206, 210, 214), alpha_cut=True)),
    "grating": dict(tile=(0.6, 0.6), px=64, painter=lambda c: mesh_grid(c, 10, 0.28, (96, 100, 104))),
    "heli_light": dict(px=32, painter=flat_emis(0.35), emissive=(110, 255, 140)),
    # helideck night lighting: small fixtures + warm core/under-truss wash matching roof.jpg
    "deck_lit": dict(tile=((2 * HS - DECK_W) / 7, DECK_W), px=128, painter=deck_glow),
    "heli_light_y": dict(px=32, painter=flat_emis(0.35), emissive=(255, 214, 90)),
    "obst_light": dict(px=32, painter=flat_emis(0.6), emissive=(255, 58, 40)),
    "under_light": dict(px=32, painter=flat_emis(0.45), emissive=(255, 218, 155)),
    "core_glow": dict(px=32, painter=lambda c: c.emis.__setitem__(Ellipsis, (0.35 * (1.0 - 0.55 * c.v)).astype(np.float32)),
                      emissive=(255, 214, 145)),
}

A = K.Atlas(size=4096, pad=16)
for name, color, metal, gloss, px in (
        ("stone", (102, 96, 94), 0.0, 0.35, 128),        # warm dark granite (user-02/03/05, lightened per gate)
        ("stone_trim", (98, 92, 90), 0.0, 0.35, 64),     # granite trim / podium ledges
        ("pale", (238, 235, 226), 0.0, 0.32, 128),       # sunlit warm cream limestone (fixes gate COLOR_OFF)
        ("crown_white", (236, 237, 234), 0.15, 0.42, 64), # helipad rim / core / bridge frame
        ("core_glow", (236, 232, 222), 0.1, 0.4, 32),    # illuminated helipad central core
        ("deck_under", (90, 94, 100), 0.35, 0.4, 64),    # slim underside deck plate
        ("crown_glass", (128, 182, 174), 0.5, 0.9, 128), # light green reflective observatory glass (roof.jpg)
        ("obs_roof", (64, 84, 100), 0.6, 0.92, 128),     # dark blue-grey skylight glass
        ("railing", (212, 215, 218), 0.65, 0.55, 64),    # galvanized / brushed steel open rails
        ("se_glass", (142, 182, 188), 0.45, 0.92, 128),  # SE top 4-floor curtain wall (user-12-se / site.jpg)
        ("frame", (236, 237, 235), 0.3, 0.5, 64),        # white window frames
        ("louver", (232, 233, 230), 0.2, 0.4, 64),       # AC louver panels
        ("louver_back", (68, 70, 74), 0.0, 0.3, 64),
        ("roof", (132, 134, 134), 0.0, 0.3, 64),
        ("deck", (156, 158, 156), 0.0, 0.3, 64),
        ("heli_green", (74, 142, 104), 0.0, 0.25, 64),
        ("heli_white", (234, 236, 228), 0.0, 0.25, 64),
        ("pier_pink", (184, 146, 136), 0.0, 0.4, 128),
        ("canopy", (166, 168, 166), 0.2, 0.45, 128),
        ("glass", (150, 185, 180), 0.0, 0.35, 64),
        ("grey_stone", (158, 156, 152), 0.0, 0.3, 128),
        ("pale_trim", (236, 233, 225), 0.0, 0.32, 64),
        ("grey_trim", (156, 154, 148), 0.0, 0.3, 64),
        ("heli_net", (156, 160, 164), 0.6, 0.45, 64),    # open alpha-cut perimeter mesh
        ("grating", (142, 146, 148), 0.6, 0.35, 64),     # access platform / stair treads
        ("heli_light", (90, 230, 120), 0.0, 0.6, 32),
        ("clerestory", (44, 58, 66), 0.5, 0.9, 128),
        ("vestibule", (46, 62, 66), 0.3, 0.9, 1024),
        ("soffit", (206, 208, 204), 0.0, 0.3, 256),
        ("ent_light", (250, 240, 220), 0.0, 0.6, 32),
        ("soil", (62, 50, 40), 0.0, 0.1, 64),
        ("foliage", (52, 86, 46), 0.0, 0.15, 64),
        ("deck_lit", (156, 158, 156), 0.0, 0.3, 128),
        ("heli_light_y", (240, 208, 96), 0.0, 0.6, 32),
        ("obst_light", (226, 62, 50), 0.0, 0.6, 32),
        ("flood_light", (246, 244, 234), 0.0, 0.6, 32),
        ("windsock", (236, 112, 44), 0.0, 0.2, 32),
        ("under_light", (250, 236, 210), 0.0, 0.6, 32),
        ("window", (70, 110, 110), 0.0, 0.9, 1024)):
    A.add(name, color=color, ctrl=(0, 0, 0), metal=metal, gloss=gloss, **dict(dict(px=px), **TEX.get(name, {})))

WS = K.WindowSet()
LIT_CELLS = 7                # of the 5 x 5 window-texture cells are lit at night (28 % of the windows)


def window(mb, stage, axis, c, s, a0, a1, z0, z1, floor, unit, mull=(0.38,), jambs=(True, True)):
    """_Win quad + (main only) projecting white frame, sill and painted mullions/transom.
    jambs=(False, ..) drops the jamb at that end (corner window meeting a corner post).
    On the refuge floor every opening is a louver instead (Naver VR tour: window-less band at mid height)."""
    if floor == REF_F:
        louver(mb, stage, axis, c, s, a0, a1, z0 - 0.35, z1)
        return
    if stage == 0:
        # the kit puts a window in grid cell ((floor * units + unit) * 7) % 25; with units = 25 that is 7 * unit % 25,
        # so unit = 18 * cell % 25 (18 = 1/7 mod 25) sends it to a pseudo-random cell chosen here
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
        for u in mull:  # never at u=0.5 so the window centre stays unblocked
            a = a0 + (a1 - a0) * u
            K.paint(mb, axis, c, s, a - 0.03, a + 0.03, z0, z1, "frame", layer=lm)
        zt = z0 + 0.55 * (z1 - z0)
        K.paint(mb, axis, c, s, a0, a1, zt, zt + 0.05, "frame", layer=lm + 1)


def louver(mb, stage, axis, c, s, a0, a1, z0, z1):
    if stage == 0:
        K.axbox(mb, axis, c, s, a0, a1, 0, 0.08, z0, z1, "louver")   # slats baked into the texture


WIDE = (0.1, 0.4, 0.46, 0.54, 0.6, 0.9)   # two sash units (narrow + wide each), paired mullion at joint
PAIR = (0.18, 0.46, 0.54, 0.82)          # shorter windows: narrow, wide | wide, narrow
BAYW = 0.35                              # right-wing bay window projection
TZ = 1.05                                # raised terrace / lobby floor level = porch landing (7 x 0.15 m)
CW = 0.15                                # corner window stops this far from the wall corner; post fills gap

SE_GLASS = (7.25, 16.35)                 # SE top 4-floor glazed curtain wall Y-range on -13.70 center face
SE_FLANKS_WINS = ((4.25, 6.60, PAIR), (17.00, 19.35, PAIR))  # flanking windows on center face (always kept)
SE_MID_WINS = ((7.40, 8.20, ()), (8.55, 10.15, (0.38,)), (13.25, 14.05, ()), (14.40, 16.05, (0.38,)))
SE_MID_LOUVER = (10.80, 12.60)
SE_REC_WINS = ((0.70, 2.35, (0.38,)), (21.25, 23.00, (0.38,)))

NW_MAIN_WINS = ((5.25, 7.65, PAIR), (14.55, 17.25, PAIR), (18.45, 22.45, WIDE))
NW_NOTCH_WINS = ((9.45, 10.35, ()), (12.05, 12.95, ()))

BACK_WINS = ((-11.20, -8.40, PAIR), (-7.45, -5.85, (0.38,)), (-5.05, -3.20, PAIR),
             (1.15, 4.10, PAIR), (5.05, 6.55, (0.38,)), (7.60, 12.40, WIDE))

GROUND_SE = ((4.35, 6.75, PAIR), (7.75, 10.45, PAIR), (14.10, 16.45, PAIR), (17.20, 19.30, (0.38,)))
GROUND_SE_LOUVER = (11.15, 13.35)          # ground-floor white double louver doors (user-07-side)
GROUND_NE_LOBBY = ((0.95, 2.70, PAIR), (3.05, 4.80, PAIR))  # 1F right-wing lobby glazing above terrace (sv-front)
GROUND_NW = ((1.20, 4.40, PAIR), (5.20, 7.60, PAIR), (14.80, 17.50, PAIR), (18.60, 22.00, WIDE))
GROUND_BACK = ((-11.00, -8.20, PAIR), (-5.40, -3.40, (0.38,)), (1.40, 4.20, PAIR), (7.80, 12.20, WIDE))


def corner_bay(mb, stage, z, f, u):
    """Front-right (NE/NW) corner window wrapping onto NW (+X) face (user-04)."""
    z0, z1 = z + SILL, z + HEAD
    window(mb, stage, "y", 0.0, -1, 11.90, NW_X - CW, z0, z1, f, u, WIDE, jambs=(True, False))
    window(mb, stage, "x", NW_X, 1, CW, 4.35, z0, z1, f, u + 1, PAIR, jambs=(False, True))
    if stage == 0:
        K.corner_post(mb, NW_X, 0.0, 1, -1, 0.12, z0, z1, "frame")
    return u + 2


def floor_facade(mb, stage, f):
    """Windows and louvers of one upper floor f (f >= 1) matching OSM stepped faces."""
    z = zf(f)
    z0, z1, u = z + SILL, z + HEAD, 0
    # Left front (NE) wing (-12.00..-2.50): floor 1 is solid grey granite apron over pilotis (user-03)
    if f > 1:
        window(mb, stage, "y", 0.0, -1, -11.20, -7.30, z0, z1, f, u, WIDE); u += 1
        louver(mb, stage, "y", 0.0, -1, -6.40, -5.20, z + 0.4, z1)
        window(mb, stage, "y", 0.0, -1, -4.45, -3.05, z0, z1, f, u, PAIR); u += 1
    # Right front (NE) wing (+0.40..+13.60)
    u = corner_bay(mb, stage, z, f, u)
    window(mb, stage, "y", 0.0, -1, 8.00, 11.25, z0, z1, f, u, WIDE); u += 1
    window(mb, stage, "y", 0.0, -1, 4.70, 7.25, z0, z1, f, u, PAIR); u += 1
    louver(mb, stage, "y", 0.0, -1, 2.85, 4.05, z + 0.4, z1)
    if stage == 0 and f != REF_F:
        mb.box(1.05, 2.35, -BAYW, 0.0, z0 - 0.1, z1 + 0.1, dict(left="glass", right="glass", default="frame"),
               skip=("back",))
    window(mb, stage, "y", 0.0 if f == REF_F else -BAYW, -1, 1.15, 2.25, z0, z1, f, u); u += 1
    # Front slot cheeks & twin back windows
    window(mb, stage, "x", FS_X0, 1, 0.22, 0.94, z0, z1, f, u); u += 1
    window(mb, stage, "x", FS_X1, -1, 0.22, 0.94, z0, z1, f, u); u += 1
    window(mb, stage, "y", FS_D, -1, -2.05, -1.25, z0, z1, f, u); u += 1
    window(mb, stage, "y", FS_D, -1, -0.85, -0.05, z0, z1, f, u); u += 1
    # SE (-X) facade: recessed outer corners + projecting center (top 4 floors center owned by se_curtain)
    for a0, a1, m in SE_REC_WINS:
        window(mb, stage, "x", SE_X, -1, a0, a1, z0, z1, f, u, m); u += 1
    for a0, a1, m in SE_FLANKS_WINS:
        window(mb, stage, "x", SE_XOUT, -1, a0, a1, z0, z1, f, u, m); u += 1
    if f < NF - 4:
        for a0, a1, m in SE_MID_WINS:
            window(mb, stage, "x", SE_XOUT, -1, a0, a1, z0, z1, f, u, m); u += 1
        louver(mb, stage, "x", SE_XOUT, -1, *SE_MID_LOUVER, z + 0.4, z1)
    # NW (+X) facade: outer wings + center notch
    for a0, a1, m in NW_MAIN_WINS:
        window(mb, stage, "x", NW_X, 1, a0, a1, z + 1.05, z1, f, u, m); u += 1
    for a0, a1, m in NW_NOTCH_WINS:
        window(mb, stage, "x", NW_NIN, 1, a0, a1, z + 1.05, z1, f, u, m); u += 1
    # SW (+Y) back facade + back slot
    for a0, a1, m in BACK_WINS:
        window(mb, stage, "y", D, 1, a0, a1, z0, z1, f, u, m); u += 1
    window(mb, stage, "y", D - BS_D, 1, -1.95, -0.55, z0, z1, f, u, ()); u += 1


def ground_floor(mb, stage):
    zs0, zs1, u = SILL, GH - 0.8, 0
    # Left front pilotis stays open (no glazing); slot rear door off raised terrace + 1F NE lobby windows (sv-front)
    window(mb, stage, "y", FS_D, -1, -1.85, -0.25, TZ + 0.05, TZ + 2.35, 0, u); u += 1
    for idx, (a0, a1, m) in enumerate(GROUND_NE_LOBBY):
        window(mb, stage, "y", 0.0, -1, a0, a1, TZ + 0.12, GH - 0.90, 0, 1 - idx, m)
    for a0, a1, m in GROUND_SE:
        window(mb, stage, "x", SE_XOUT, -1, a0, a1, zs0, zs1, 0, u, m); u += 1
    louver(mb, stage, "x", SE_XOUT, -1, *GROUND_SE_LOUVER, 0.25, zs1 - 0.15)
    for a0, a1, m in GROUND_NW:
        window(mb, stage, "x", NW_X, 1, a0, a1, zs0, zs1, 0, u, m); u += 1
    for a0, a1, m in GROUND_BACK:
        window(mb, stage, "y", D, 1, a0, a1, zs0, zs1, 0, u, m); u += 1


def ledges(mb, z, p, t, f):
    """Per-floor ledges wrapping the 20-vertex OSM footprint with zero corner overlaps."""
    podium = f < PALE_F or f == NF
    fm = "stone_trim" if f < PALE_F else "pale_trim"
    # Front (NE) wings: full height on all 50 floors (sv-front / user-10)
    mb.box(SE_X - p, FS_X0, -p, 0.0, z, z + t, fm, skip=("back",))
    if podium:
        mb.box(FS_X1, NW_X, -p, 0.0, z, z + t, fm, skip=("back", "right"))
        mb.box(NW_X, NW_X + p, -p, NW_Y0, z, z + t, fm, skip=("left",))
        mb.box(NW_X, NW_X + p, NW_Y1, D, z, z + t, fm, skip=("left", "back"))
    else:
        mb.box(FS_X1, NW_X, -p, 0.0, z, z + t, fm, skip=("back",))
    # SE (-X): recessed corners full height; center full on podium only, flanks-only upper/cornice (clear of se_crown)
    se_m = "stone_trim" if f < NF else "pale_trim"
    mb.box(SE_X - p, SE_X, 0.0, SE_Y0 - p, z, z + t, se_m, skip=("front", "back", "right"))
    mb.box(SE_X - p, SE_X, SE_Y1 + p, D, z, z + t, se_m,
           skip=("front", "right") + (("back",) if podium else ()))
    mb.box(SE_XOUT - p, SE_X, SE_Y0 - p, SE_Y0, z, z + t, se_m, skip=("back",))
    mb.box(SE_XOUT - p, SE_X, SE_Y1, SE_Y1 + p, z, z + t, se_m, skip=("front",))
    if f < PALE_F:
        mb.box(SE_XOUT - p, SE_XOUT, SE_Y0, SE_Y1, z, z + t, "stone_trim", skip=("front", "back", "right"))
    else:
        mb.box(SE_XOUT - p, SE_XOUT, SE_Y0, SE_GLASS[0] - 0.1, z, z + t, se_m, skip=("front", "right"))
        mb.box(SE_XOUT - p, SE_XOUT, SE_GLASS[1] + 0.1, SE_Y1, z, z + t, se_m, skip=("back", "right"))
    # SW (+Y) back: wide NW-side wing (+X) carries ledges full height; SE-side (-X) podium/cornice only
    if podium:
        mb.box(SE_X - p, BS_X0, D, D + p, z, z + t, se_m, skip=("front",))
        mb.box(BS_X1, NW_X + p, D, D + p, z, z + t, fm, skip=("front",))
    else:
        mb.box(BS_X1, NW_X, D, D + p, z, z + t, "pale_trim", skip=("front",))


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
    """Band of n quads between polygon (r0, z0) and polygon (r1, z1); uses mb.quad so sloped rings never tile-clip."""
    uv4 = A.uv(region)
    for i in range(n):
        a, b = rot + 2 * math.pi * i / n, rot + 2 * math.pi * (i + 1) / n
        q = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0), (cx + r0 * math.cos(b), cy + r0 * math.sin(b), z0),
             (cx + r1 * math.cos(b), cy + r1 * math.sin(b), z1), (cx + r1 * math.cos(a), cy + r1 * math.sin(a), z1)]
        mb.quad(q[::-1] if flip else q, uv4, region)


# Crown & helipad (user-09 / audit_dong_aerials / site.jpg / roof.jpg):
# Helipad sits over the NW (+X) half (HX=5.0, HY=12.6, HS=7.4 -> 14.8 x 14.8 m), leaving NE front (0..4.1) & SE
# terrace (-13.7..-2.4) open. Thin deck supported on slim core + 8 open V-struts (no solid black inverted pyramid),
# open post+bar perimeter safety rails, alpha-cut safety net + outrigger ribs, and SE steel bridge frame.
HX, HY = 5.0, 12.6
HCORE = 1.25
OZ = H + 5.00                                # observatory roof (0.65 plinth + 3.95 glass + 0.40 coping)
HZU = H + 9.06                               # thin deck underside (4.06 m clear truss air gap above OZ)
HZT = H + 9.40                               # deck top (open rail top ~ 159.5 m)
OX0, OX1, OY0, OY1 = -3.40, 11.80, 4.20, 20.40  # observatory glass box kept strictly inside NW notch (12.05)
SQ = math.pi / 4
RC = HS * math.sqrt(2)
NET = 1.05                                   # perimeter safety net width
PX0 = HX - HS - NET                          # safety-net outer SE edge (-3.45)
BR_X0, BR_Y0, BR_Y1 = -5.50, 8.80, 16.40     # SE steel bridge truss bay (user-09)


def crown(mb, stage):
    n = (32, 20, 10)[stage]
    core_reg = "core_glow" if stage < 2 else "crown_white"
    ring(mb, HX, HY, HCORE, H, HCORE, OZ, "crown_white", n)                  # lower shaft inside obs
    ring(mb, HX, HY, HCORE, OZ, HCORE, HZU, core_reg, n)                      # warm-lit open shaft above obs
    ring(mb, HX, HY, RC, HZU, RC, HZT, "crown_white", 4, rot=SQ)              # thin deck fascia rim
    ring(mb, HX, HY, RC, HZT, 0.85, HZT, "deck", 4, rot=SQ)                   # grey perimeter deck band
    q_bot = K.up_quad([(HX - HS, HY - HS, HZU), (HX + HS, HY - HS, HZU),
                       (HX + HS, HY + HS, HZU), (HX - HS, HY + HS, HZU)])
    mb.quad(q_bot[::-1], A.uv("deck_under"), "deck_under")                    # flat deck soffit (shows open V-struts!)
    pad_s = HS - DECK_W
    mb.box(HX - pad_s, HX + pad_s, HY - pad_s, HY + pad_s, HZT, HZT + 0.03, "heli_green", skip=("bottom",))
    observatory(mb, stage)
    se_crown(mb, stage)
    if stage < 2:
        heli_underside(mb, stage)
        zt = HZT + 0.03
        s = pad_s / 6.6
        for x0, x1, y0, y1 in ((-6.1, -5.95, -6.1, 6.1), (5.95, 6.1, -6.1, 6.1), (-5.95, 5.95, -6.1, -5.95),
                               (-5.95, 5.95, 5.95, 6.1), (-1.7, -1.4, -2.3, 2.3), (1.4, 1.7, -2.3, 2.3),
                               (-1.4, 1.4, -0.15, 0.15)):
            mb.box(HX + x0 * s, HX + x1 * s, HY + y0 * s, HY + y1 * s, zt, zt + 0.03, "heli_white", skip=("bottom",))
        for i in range(32):
            a, b = 2 * math.pi * i / 32, 2 * math.pi * (i + 1) / 32
            mb.quad([(HX + r * math.cos(t), HY + r * math.sin(t), zt + 0.04)
                     for r, t in ((3.9, a), (3.9, b), (3.76, b), (3.76, a))], A.uv("heli_white"), "heli_white")
        heli_net(mb, stage)
        heli_lights(mb, stage)
        heli_access(mb, stage)


def se_crown(mb, stage):
    """SE (-X) top 4-floor glazed curtain wall module + stepped crown parapet wings (user-12-se / site.jpg)."""
    z0, zt = zf(NF - 4), H + 2.35
    y0, y1 = SE_GLASS
    # Proud 0.22 m curtain wall module along SE center [-13.92, -13.70]; skip main wall face below H
    mb.box(SE_XOUT - 0.22, SE_XOUT, y0, y1, z0, H,
           dict(left="se_glass", default="deck_under"), skip=("right", "top"))
    # Above H: enclosed rooftop glazed lantern box up to H + 2.35 m
    mb.box(SE_XOUT - 0.22, SE_XOUT + 0.35, y0, y1, H, zt,
           dict(left="se_glass", right="pale", top="roof", default="deck_under"), skip=("bottom",))
    if stage < 2:
        # Stepped shoulder piers + higher parapet framing the glazed lantern (site.jpg)
        for ya, yb in ((SE_Y0, y0), (y1, SE_Y1)):
            mb.box(SE_XOUT, SE_XOUT + 0.35, ya, yb, H, H + 1.85, "pale", skip=("bottom",))


def observatory(mb, stage):
    """Glass observatory under the deck (kept within NW_NIN=12.05): taller clear glass box glowing at night."""
    zp, zc = H + 0.65, OZ - 0.40
    mb.box(OX0, OX1, OY0, OY1, H, zp, "pale", skip=("bottom",))
    g = 0.14
    mb.box(OX0 + g, OX1 - g, OY0 + g, OY1 - g, zp, zc, "crown_glass", skip=("bottom", "top"))
    mb.box(OX0, OX1, OY0, OY1, zc, OZ, dict(top="roof", default="crown_white"))
    if stage > 1:
        return
    # Skylight lantern on SW strip outside the deck shadow
    xd, yd, t = HX + HS + 0.25, HY + HS + 0.25, 0.45
    if yd < OY1 - 0.4:
        mb.box(OX0 + 0.6, min(xd, OX1 - 0.3), yd, OY1 - 0.3, OZ, OZ + t,
               dict(top="obs_roof", default="crown_white"), skip=("bottom",))
    if stage > 0:
        return
    for axis, c, s, a0, a1 in (("y", OY0 + g, -1, OX0 + g, OX1 - g), ("y", OY1 - g, 1, OX0 + g, OX1 - g),
                               ("x", OX0 + g, -1, OY0 + g, OY1 - g), ("x", OX1 - g, 1, OY0 + g, OY1 - g)):
        n = int((a1 - a0) / 2.4)
        for k in range(1, n + 1):
            a = a0 + k * (a1 - a0) / (n + 1)
            K.axbox(mb, axis, c, s, a - 0.05, a + 0.05, 0, 0.12, zp, zc, "crown_white", skip=("top", "bottom"))


def heli_underside(mb, stage):
    """Open steel truss underside (roof.jpg / site.jpg): collar node on OZ shaft, 8 long diagonal V-struts fanning
    cleanly to the outer deck perimeter beam, radial steel under-beams, warm night wash lights."""
    zc0, zc1 = OZ + 0.40, OZ + 1.00
    n = 32 if stage == 0 else 16
    ring(mb, HX, HY, HCORE + 0.20, zc0, HCORE + 0.20, zc1, "crown_white", n)
    ring(mb, HX, HY, HCORE + 0.20, zc1, HCORE, zc1, "crown_white", n)
    ring(mb, HX, HY, HCORE + 0.20, zc0, HCORE, zc0, "crown_white", n, flip=True)
    # 8 exposed diagonal V-struts to 0.86 * HS perimeter node (cleanly visible against the sky!)
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        ca, sa = math.cos(a), math.sin(a)
        k = max(abs(ca), abs(sa))
        d1 = 0.86 * HS
        prism(mb, (HX + (HCORE + 0.10) * ca, HY + (HCORE + 0.10) * sa, (zc0 + zc1) * 0.5),
              (HX + d1 / k * ca, HY + d1 / k * sa, HZU - 0.06), 0.34, "crown_white")
    if stage > 0:
        return
    # Radial under-deck box beams + collar wash lights + perimeter soffit downlights
    for i in range(8):
        a = 2 * math.pi * i / 8
        ca, sa = math.cos(a), math.sin(a)
        k = max(abs(ca), abs(sa))
        prism(mb, (HX + 1.4 / k * ca, HY + 1.4 / k * sa, HZU - 0.14),
              (HX + (HS - 0.1) / k * ca, HY + (HS - 0.1) / k * sa, HZU - 0.14), 0.20, "crown_white")
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        x, y = HX + (HCORE + 0.28) * math.cos(a), HY + (HCORE + 0.28) * math.sin(a)
        mb.box(x - 0.18, x + 0.18, y - 0.18, y + 0.18, zc1, zc1 + 0.12, "under_light", skip=("bottom",))
        k = max(abs(math.cos(a)), abs(math.sin(a)))
        ux, uy = HX + 5.2 / k * math.cos(a), HY + 5.2 / k * math.sin(a)
        mb.box(ux - 0.24, ux + 0.24, uy - 0.24, uy + 0.24, HZU - 0.12, HZU, "under_light", skip=("top",))


def heli_net(mb, stage):
    """Open alpha-cut steel safety net round NE/NW/SW deck edges + open post+bar perimeter rails."""
    z0 = z1 = HZT - 0.09
    xw0, xw1 = HX - HS, HX + HS
    yw0, yw1 = HY - HS, HY + HS
    nx1, ny0, ny1 = xw1 + NET, yw0 - NET, yw1 + NET
    for xa, xb, ya, yb in (
            (xw1, nx1, ny0, ny1),               # NW (+X) net
            (xw0, xw1, yw1, ny1),               # SW (+Y) net
            (xw0, xw1, ny0, yw0),               # NE (-Y) net
            (PX0, xw0, ny0, BR_Y0),             # SE (-X) net front of bridge
            (PX0, xw0, BR_Y1, ny1),             # SE (-X) net back of bridge
    ):
        mb.quad([(xa, ya, z1), (xb, ya, z1), (xb, yb, z1), (xa, yb, z1)], A.uv("heli_net"), "heli_net")
        mb.quad([(xb, ya, z0), (xa, ya, z0), (xa, yb, z0), (xb, yb, z0)], A.uv("heli_net"), "heli_net")
    # Slim steel outer perimeter frame rails & diagonal outrigger brackets
    corners = [(PX0, ny0), (nx1, ny0), (nx1, ny1), (PX0, ny1)]
    for i in range(4):
        (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
        prism(mb, (ax, ay, z1 + 0.02), (bx, by, z1 + 0.02), 0.06, "railing")
        if stage == 0:
            prism(mb, (ax, ay, HZT + 0.72), (bx, by, HZT + 0.72), 0.045, "railing")
            prism(mb, (ax, ay, HZT + 0.34), (bx, by, HZT + 0.34), 0.035, "railing")
            n_posts = max(3, round(math.hypot(bx - ax, by - ay) / 2.2))
            for k in range(n_posts):
                t = k / n_posts
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                mb.box(px - 0.025, px + 0.025, py - 0.025, py + 0.025, z0, HZT + 0.74, "railing", skip=("bottom",))
    if stage == 0:
        for y in np.linspace(yw0 + 0.6, yw1 - 0.6, 6):
            prism(mb, (xw1, y, HZU), (nx1, y, z0), 0.055, "crown_white")
            if y < BR_Y0 or y > BR_Y1:
                prism(mb, (xw0, y, HZU), (PX0, y, z0), 0.055, "crown_white")
        for x in np.linspace(xw0 + 0.6, xw1 - 0.6, 6):
            prism(mb, (x, yw0, HZU), (x, ny0, z0), 0.055, "crown_white")
            prism(mb, (x, yw1, HZU), (x, ny1, z0), 0.055, "crown_white")


def heli_lights(mb, stage):
    """Helideck night lighting: green perimeter lights, yellow touchdown circle, low floodlights, red obst lights."""
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
                mb.box(x - 0.09, x + 0.09, y - 0.09, y + 0.09, z, z + 0.09, "heli_light", skip=("bottom",))
    if stage > 0:
        return
    for i in range(16):
        a = 2 * math.pi * (i + 0.5) / 16
        x, y = HX + 3.83 * math.cos(a), HY + 3.83 * math.sin(a)
        mb.box(x - 0.07, x + 0.07, y - 0.07, y + 0.07, HZT + 0.07, HZT + 0.13, "heli_light_y", skip=("bottom",))
    body = dict(default="railing", top="railing")
    zr = HZT + 0.72
    for t in (-3.6, 3.6):
        mb.box(HX + t - 0.25, HX + t + 0.25, y0 - NET - 0.10, y0 - NET + 0.08, zr, zr + 0.18,
               dict(body, back="flood_light"), skip=("bottom",))
        mb.box(HX + t - 0.25, HX + t + 0.25, y1 + NET - 0.08, y1 + NET + 0.10, zr, zr + 0.18,
               dict(body, front="flood_light"), skip=("bottom",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = HX + sx * (HS + NET - 0.04), HY + sy * (HS + NET - 0.04)
            mb.box(x - 0.10, x + 0.10, y - 0.10, y + 0.10, zr, zr + 0.22, "obst_light", skip=("bottom",))
    mx, my, zn = x1 + NET - 0.30, y0 - NET + 0.30, HZT - 0.08
    mb.box(mx - 0.05, mx + 0.05, my - 0.05, my + 0.05, zn, zn + 3.0, "crown_white", skip=("bottom", "top"))
    mb.box(mx - 0.09, mx + 0.09, my - 0.09, my + 0.09, zn + 3.0, zn + 3.2, "obst_light", skip=("bottom",))
    mb.box(mx + 0.05, mx + 0.90, my - 0.15, my + 0.15, zn + 2.4, zn + 2.74, "windsock", skip=("left",))
    mb.box(mx + 0.90, mx + 1.45, my - 0.10, my + 0.10, zn + 2.46, zn + 2.68, "windsock", skip=("left",))


def heli_access(mb, stage):
    """White steel access bridge frame on SE (-X) edge (BR_X0..HX-HS) + open steel switchback stair down to
    the main concrete roof (user-09 aerial / L508 TODO)."""
    xw0 = HX - HS
    zt, zb = HZT - 0.02, HZT - 0.16
    mb.box(BR_X0, xw0, BR_Y0, BR_Y1, zb, zt, "grating", skip=("right",))
    for y in (BR_Y0 + 0.06, BR_Y1 - 0.06):
        prism(mb, (BR_X0, y, zb - 0.08), (xw0, y, zb - 0.08), 0.14, "crown_white")
    prism(mb, (BR_X0 + 0.06, BR_Y0 + 0.13, zb - 0.08), (BR_X0 + 0.06, BR_Y1 - 0.13, zb - 0.08), 0.14, "crown_white")
    for y in (BR_Y0 + 0.12, (BR_Y0 + BR_Y1) * 0.5, BR_Y1 - 0.12):
        mb.box(BR_X0, BR_X0 + 0.20, y - 0.10, y + 0.10, H, zb - 0.15, "crown_white", skip=("bottom", "top"))
    if stage > 0:
        return
    prism(mb, (BR_X0 + 0.10, BR_Y0 + 0.15, H + 0.4), (BR_X0 + 0.10, BR_Y1 - 0.15, zb - 0.2), 0.08, "crown_white")
    prism(mb, (BR_X0 + 0.24, BR_Y1 - 0.15, H + 0.4), (BR_X0 + 0.24, BR_Y0 + 0.15, zb - 0.2), 0.08, "crown_white")
    for p0, p1 in (((BR_X0, BR_Y0), (xw0, BR_Y0)), ((BR_X0, BR_Y1), (xw0, BR_Y1)),
                   ((BR_X0, BR_Y0 + 1.10), (BR_X0, BR_Y1))):
        for dz in (0.42, 0.85):
            prism(mb, (p0[0], p0[1], zt + dz), (p1[0], p1[1], zt + dz), 0.04, "railing")
    sx0, sx1 = BR_X0 - 1.20, BR_X0
    ys, yn, n = BR_Y0 + 1.10, BR_Y1 - 0.90, 22
    zm = (H + zt) * 0.5
    tr, ri = (yn - ys) / n, (zm - H) / n
    for (xa, xb), y0, z0, dy in (((sx0 - 1.25, sx0 - 0.10), ys, H, 1), ((sx0, sx1), yn, zm, -1)):
        for i in range(n):
            ya, yb = sorted((y0 + dy * i * tr, y0 + dy * (i + 1) * tr))
            ztop = z0 + (i + 1) * ri
            mb.box(xa, xb, ya + 0.02, yb - 0.02, ztop - 0.05, ztop, "grating")
        y1, z1 = y0 + dy * n * tr, z0 + n * ri
        for x in (xa + 0.08, xb - 0.08):
            prism(mb, (x, y0, z0 - 0.12), (x, y1, z1 - 0.12), 0.10, "crown_white")
        xo = xa if dy > 0 else xb
        prism(mb, (xo, y0, z0 + 0.88), (xo, y1, z1 + 0.88), 0.045, "railing")
        for f in (0.15, 0.5, 0.85):
            yy, zz = y0 + dy * f * (n * tr), z0 + f * n * ri
            mb.box(xo - 0.02, xo + 0.02, yy - 0.02, yy + 0.02, zz, zz + 0.90, "railing", skip=("bottom",))
    mb.box(sx0 - 1.25, sx1, yn, yn + 1.15, zm - 0.12, zm, "grating")
    mb.box(sx0, sx1, BR_Y0, ys, zt - 0.12, zt, "grating", skip=("right",))
    for x, y, z in ((sx0 - 1.15, yn + 1.05, zm), (sx1 - 0.10, yn + 1.05, zm)):
        mb.box(x - 0.09, x + 0.09, y - 0.09, y + 0.09, H, z - 0.12, "crown_white", skip=("bottom", "top"))


EY = -4.2                    # porch front (user entrance photos; depth estimated)
EZ0, EZB, EZC, EZT = 3.8, 4.65, 5.45, 5.85   # porch soffit / pale band top / clerestory top / slab top (estimated)
# slab top stays below the floor-1 window sills (frame bottom 5.89): the porch must not cut into them (user, in game)
ST_N, ST_R, ST_T = 7, 0.15, 0.36          # stair: 7 risers of 0.15 m, 0.36 m treads (counted from the photo)


def entrance(mb, stage):
    """Entrance porch on the right NE wing (+5.30..+13.60, pink pier flush with NW_X corner): proud dark hood
    framing recessed pale fascia & 2-tier clerestory on front and both sides, behind-pier ramp landing,
    right-portal granite planter with shrubs, 5-bar guardrails, protruding revolving door & sidelight vestibule."""
    ZS = EZT - 0.2                                    # underside of the roof slab
    yl, zl = EY + ST_N * ST_T, ST_N * ST_R
    y_beam = EY + 0.35
    if stage == 2:
        mb.box(5.30, 6.50, EY - 0.10, EY + 1.15, 0, ZS, "stone_trim", skip=("bottom", "top"))
        mb.box(5.40, 13.45, EY, 0.0, EZ0, ZS,
               dict(front="pale", right="pale", left="pale", bottom="soffit", top="stone_trim"),
               skip=("back", "top"))
        mb.box(11.60, 13.60, EY - 0.20, EY + 1.80, 0, ZS,
               dict(front="pier_pink", right="stone", left="stone_trim", default="pier_pink"),
               skip=("bottom", "top"))
        mb.box(5.20, 13.70, EY - 0.20, 0.0, ZS, EZT, dict(top="roof", default="stone_trim"), skip=("back",))
        return

    # Left dark granite pier (base plinth + shaft) & rear canopy wing back to tower wall
    mb.box(5.26, 6.54, EY - 0.14, EY + 1.19, 0.0, 0.16, "stone_trim", skip=("bottom",))
    mb.box(5.30, 6.50, EY - 0.10, EY + 1.15, 0.16, ZS, "stone_trim", skip=("bottom", "top"))
    mb.box(5.40, 6.50, EY + 1.15, 0.0, EZ0, ZS,
           dict(left="pale", bottom="soffit", default="pale"), skip=("back", "top", "front", "right"))

    # Center recessed beam (0.35 m behind proud dark hood & piers) + right-side canopy extension
    mb.box(6.50, 11.60, y_beam, 0.0, EZ0, ZS,
           dict(front="pale", bottom="soffit", default="pale"), skip=("back", "top", "left", "right"))
    mb.box(11.60, 13.45, EY + 1.80, 0.0, EZ0, ZS,
           dict(right="pale", bottom="soffit", default="pale"), skip=("back", "top", "front", "left"))

    # Right corner pier: base plinth + front pink granite wrap (wraps onto +X 0.5 m) + rear dark granite (user-04)
    mb.box(11.56, 13.64, EY - 0.24, EY + 1.84, 0.0, 0.16, "stone_trim", skip=("bottom",))
    mb.box(11.60, 13.60, EY - 0.20, EY + 0.30, 0.16, ZS,
           dict(front="pier_pink", right="pier_pink", left="stone_trim", default="pier_pink"),
           skip=("bottom", "top", "back"))
    mb.box(11.60, 13.60, EY + 0.30, EY + 1.80, 0.16, ZS,
           dict(right="stone", left="stone_trim", back="stone", default="stone"),
           skip=("bottom", "top", "front"))

    # Proud dark granite roof slab capping whole portico cleanly to tower wall
    mb.box(5.20, 13.70, EY - 0.20, 0.0, ZS, EZT, dict(top="roof", default="stone_trim"), skip=("back",))

    # Front & side 2-tier clerestory glazing with mullions + dark stone top fascia (non-overlapping paint layers)
    z_mid = (EZB + EZC) * 0.5
    for axis, c, s, a0, a1, n_bays in (("y", y_beam, -1, 6.50, 11.60, 4),
                                       ("x", 13.45, 1, EY + 1.80, 0.0, 3),
                                       ("x", 5.40, -1, EY + 1.15, 0.0, 3)):
        K.paint(mb, axis, c, s, a0, a1, EZC, ZS, "stone", layer=2)
        K.paint(mb, axis, c, s, a0, a0 + 0.14, EZB + 0.06, EZC - 0.06, "stone", layer=2)
        K.paint(mb, axis, c, s, a1 - 0.14, a1, EZB + 0.06, EZC - 0.06, "stone", layer=2)
        K.paint(mb, axis, c, s, a0 + 0.14, a1 - 0.14, EZB + 0.06, EZC - 0.06, "clerestory", layer=2)
        for k in range(1, n_bays):
            am = (a0 + 0.14) + ((a1 - 0.14) - (a0 + 0.14)) * k / n_bays
            K.paint(mb, axis, c, s, am - 0.028, am + 0.028, EZB + 0.06, EZC - 0.06, "frame", layer=3)
        for zb0, zb1 in ((EZB, EZB + 0.06), (z_mid - 0.025, z_mid + 0.025), (EZC - 0.06, EZC)):
            K.paint(mb, axis, c, s, a0, a1, zb0, zb1, "frame", layer=4)

    # Stairs, landing, behind-left-pier bridge (connects ㄷ자 ramp onto landing), right cheek & portal planter
    for i in range(ST_N):
        y0 = EY + i * ST_T
        mb.box(6.50, 11.60, y0, y0 + ST_T, 0, ST_R * (i + 1), "canopy",
               skip=("bottom", "back", "left", "right"))
    mb.box(6.50, 11.60, yl, 0.0, 0, zl, "canopy", skip=("bottom", "back", "left", "right"))
    mb.box(5.30, 6.50, yl, 0.0, 0, zl, dict(top="canopy", default="stone_trim"),
           skip=("bottom", "back", "left", "right"))
    mb.box(6.15, 6.50, EY + 1.15, yl, 0, zl, "stone_trim", skip=("bottom", "front", "back"))
    mb.box(11.60, 11.88, EY + 1.80, yl, 0, 0.72, "stone_trim", skip=("bottom", "front", "back"))
    mb.box(11.60, 11.88, yl, 0.0, 0, zl, "stone_trim", skip=("bottom", "back"))
    mb.box(11.88, 13.50, EY + 1.80, 0.0, 0, 0.44, dict(top="soil", default="stone_trim"),
           skip=("bottom", "front", "left", "back"))

    # Vestibule glazing + dark granite behind-pier panel + protruding revolving door & right swing door bay
    mb.box(5.30, 6.50, -0.06, 0.0, zl, EZ0, dict(front="stone_trim", default="stone_trim"),
           skip=("bottom", "top", "back", "left", "right"))
    mb.box(6.50, 11.60, -0.06, 0.0, zl, EZ0, dict(front="vestibule", default="stone_trim"),
           skip=("bottom", "top", "back", "left", "right"))
    mb.box(7.75, 9.55, -0.52, -0.06, zl, zl + 2.32,
           dict(front="vestibule", left="vestibule", right="vestibule", default="stone_trim"),
           skip=("bottom", "top", "back"))
    mb.box(7.65, 9.65, -0.56, -0.06, zl + 2.32, zl + 2.58, "stone_trim", skip=("back",))
    mb.box(9.85, 11.35, -0.22, -0.06, zl, zl + 2.45,
           dict(front="vestibule", default="stone_trim"), skip=("bottom", "back"))

    if stage > 0:
        return

    # Shrubs inside right portal planter + stainless stair & landing railings
    for ya_s, yb_s, z_s in ((EY + 1.92, EY + 2.50, 0.86), (EY + 2.56, EY + 3.18, 1.04), (EY + 3.24, -0.08, 0.92)):
        mb.box(11.98, 13.38, ya_s, yb_s, 0.44, z_s, "foliage", skip=("bottom",))

    ya = EY + 0.20
    rail_z = lambda y: ST_R + (y - ya) / (yl - ya) * (zl - ST_R)
    # Center 2-bar handrail on stairs
    for dz in (0.90, 0.45):
        prism(mb, (9.05, ya, dz + rail_z(ya)), (9.05, yl, dz + rail_z(yl)), 0.044 if dz == 0.90 else 0.028, "railing")
    for k in range(4):
        yy = ya + k * (yl - ya - 0.1) / 3
        zb = ST_R * min(ST_N, 1 + int((yy - EY) / ST_T))
        mb.box(9.02, 9.08, yy - 0.03, yy + 0.03, zb, 0.92 + rail_z(yy), "railing", skip=("bottom",))
    # Left (6.65) and right (11.52) 5-bar guardrails (0.06 m posts > 0.044 m rails; offset at yl prevents coplanar)
    for rx in (6.65, 11.52):
        for dz in (0.90, 0.72, 0.54, 0.36, 0.18):
            rw = 0.044 if dz == 0.90 else 0.026
            prism(mb, (rx, ya, dz + rail_z(ya)), (rx, yl - 0.035, dz + rail_z(yl - 0.035)), rw, "railing")
            prism(mb, (rx, yl + 0.035, dz + zl), (rx, -0.06, dz + zl), rw, "railing")
        for k in range(4):
            yy = ya + k * (yl - ya - 0.1) / 3
            zb = ST_R * min(ST_N, 1 + int((yy - EY) / ST_T))
            mb.box(rx - 0.03, rx + 0.03, yy - 0.03, yy + 0.03, zb, 0.92 + rail_z(yy), "railing", skip=("bottom",))
        for yy in (yl, yl * 0.5, -0.06):
            mb.box(rx - 0.03, rx + 0.03, yy - 0.03, yy + 0.03, zl, zl + 0.92, "railing", skip=("bottom",))


def terrace(mb, stage):
    """'ㄷ'자 folded barrier-free ramp & raised lobby terrace: plaza entry (+2.45) -> outer lower run ->
    left U-turn mid-landing ('참' at x=-5.45..-4.15) -> center divider wall -> inner upper run ->
    lobby terrace (+0.40..+5.30) passing behind portico left pier onto landing, with 5-bar rails."""
    yl = EY + ST_N * ST_T                                     # -1.68 (matches behind-pier bridge front)
    rx_t0, rx_t1, rx_r1, rx_o1 = -5.45, -4.15, 0.40, 2.45
    yo0, yo1, yc0, yc1, yi0, yi1 = -3.05, -1.84, -1.84, -1.68, -1.68, 0.0
    z_r0, z_mid = 0.04, 0.55
    zo_at = lambda x: z_mid + max(0.0, min(1.0, (x - rx_t1) / (rx_o1 - rx_t1))) * (z_r0 - z_mid)
    zi_at = lambda x: z_mid + max(0.0, min(1.0, (x - rx_t1) / (rx_r1 - rx_t1))) * (TZ - z_mid)

    # Left U-turn mid-landing ('참') + open slot rear landing floor (front face visible above sloped upper run)
    mb.box(rx_t0, rx_t1, yo0, yi1, 0.0, z_mid, dict(top="canopy", default="stone_trim"), skip=("bottom", "right"))
    mb.box(FS_X0, FS_X1, 0.0, FS_D, 0.0, TZ, dict(top="canopy", default="stone_trim"),
           skip=("back", "left", "right", "bottom"))

    # Lower outer run (slopes +2.45 -> -4.15, z=0.04 -> 0.55)
    mb.rect([(rx_t1, yo0, z_mid), (rx_o1, yo0, z_r0), (rx_o1, yo1, z_r0), (rx_t1, yo1, z_mid)], "canopy")
    mb.rect([(rx_t1, yo0, 0.0), (rx_o1, yo0, 0.0), (rx_o1, yo0, z_r0), (rx_t1, yo0, z_mid)], "stone_trim")
    mb.rect([(rx_o1, yo0, 0.0), (rx_o1, yo1, 0.0), (rx_o1, yo1, z_r0), (rx_o1, yo0, z_r0)], "stone_trim")

    # Center sloped divider retaining wall + level terrace curb extension (yc0..yc1 = -1.84..-1.68)
    mb.rect([(rx_t1, yc0, z_mid), (rx_r1, yc0, TZ), (rx_r1, yc1, TZ), (rx_t1, yc1, z_mid)], "stone_trim")
    mb.rect([(rx_t1, yc0, 0.0), (rx_r1, yc0, 0.0), (rx_r1, yc0, TZ), (rx_t1, yc0, z_mid)], "stone_trim")
    mb.box(rx_r1, 5.30, yc0, yc1, 0.0, TZ, dict(top="canopy", default="stone_trim"),
           skip=("bottom", "left", "back"))

    # Upper inner run (slopes -4.15 -> +0.40, z=0.55 -> 1.05) + open-pilotis rear cheek (-4.15..-2.50 at y=0)
    mb.rect([(rx_t1, yi0, z_mid), (rx_r1, yi0, TZ), (rx_r1, yi1, TZ), (rx_t1, yi1, z_mid)], "canopy")
    mb.rect([(FS_X0, 0.0, 0.0), (rx_t1, 0.0, 0.0), (rx_t1, 0.0, z_mid), (FS_X0, 0.0, zi_at(FS_X0))], "stone_trim")

    # Flat upper terrace in front of 1F lobby windows (+0.40..+5.30, yl..0.0 -> meets behind-pier bridge)
    mb.box(rx_r1, 5.30, yl, 0.0, 0.0, TZ, dict(top="canopy", default="stone_trim"),
           skip=("bottom", "back", "left", "right"))

    if stage > 0:
        return

    # Continuous 5-bar guardrails + 0.06 m posts (segment endpoints inset +/-0.03 at corners/bends -> 0 coplanar)
    yo_r, xl_r, yc_r, yb_r = yo0 + 0.06, rx_t0 + 0.06, (yc0 + yc1) * 0.5, -0.06
    def _post(px, py, zb, z_top_ref=None):
        zr = zb if z_top_ref is None else z_top_ref
        mb.box(px - 0.03, px + 0.03, py - 0.03, py + 0.03, zb, zr + 0.92, "railing", skip=("bottom",))

    for dz in (0.90, 0.72, 0.54, 0.36, 0.18):
        rw = 0.044 if dz == 0.90 else 0.026
        # Outer run (-4.15..+2.35) + mid-landing outer return + left edge + back edge up to slot (-5.39..-2.53)
        prism(mb, (rx_o1 - 0.10, yo_r, dz + zo_at(rx_o1 - 0.10)), (rx_t1, yo_r, dz + z_mid), rw, "railing")
        prism(mb, (rx_t1, yo_r, dz + z_mid), (xl_r + 0.03, yo_r, dz + z_mid), rw, "railing")
        prism(mb, (xl_r, yo_r + 0.03, dz + z_mid), (xl_r, yb_r - 0.03, dz + z_mid), rw, "railing")
        prism(mb, (xl_r + 0.03, yb_r, dz + z_mid), (rx_t1, yb_r, dz + z_mid), rw, "railing")
        prism(mb, (rx_t1, yb_r, dz + z_mid), (FS_X0 - 0.03, yb_r, dz + zi_at(FS_X0 - 0.03)), rw, "railing")
        # Center divider sloped rail (-4.12..+0.37) + level terrace rail (+0.43..+6.62 -> meets stair rail at 6.65!)
        prism(mb, (rx_t1 + 0.03, yc_r, dz + zi_at(rx_t1 + 0.03)), (rx_r1 - 0.03, yc_r, dz + TZ), rw, "railing")
        prism(mb, (rx_r1 + 0.03, yc_r, dz + TZ), (6.61, yc_r, dz + TZ), rw, "railing")

    for k in range(6):
        xx = (rx_o1 - 0.10) + (rx_t1 - (rx_o1 - 0.10)) * k / 5
        _post(xx, yo_r, zo_at(xx))
    _post(xl_r, yo_r, z_mid)
    _post(xl_r, (yo_r + yb_r) * 0.5, z_mid)
    _post(xl_r, yb_r, z_mid)
    _post(rx_t1, yb_r, z_mid)
    _post(FS_X0 - 0.03, yb_r, zi_at(FS_X0 - 0.03))
    for k in range(5):
        xx = (rx_t1 + 0.03) + (rx_r1 - 0.03 - (rx_t1 + 0.03)) * k / 4
        _post(xx, yc_r, zi_at(xx))
    for xx in np.linspace(1.60, 6.20, 4):
        _post(xx, yc_r, TZ)


def entrance_extras(mb):
    """Warm pier wall sconces (inner + right outer corner) and foreground granite planter with shrubs."""
    mb.box(6.50, 6.56, EY + 0.30, EY + 0.60, 2.40, 2.75, "ent_light", skip=("left",))
    mb.box(11.54, 11.60, EY + 0.30, EY + 0.60, 2.40, 2.75, "ent_light", skip=("right",))
    mb.box(13.60, 13.68, EY + 0.80, EY + 1.00, 3.05, 3.35, dict(default="stone_trim", bottom="ent_light"),
           skip=("left",))
    # Low granite planter & disjoint evergreens beside plaza ramp entry & terrace wall
    mb.box(2.75, 5.15, -3.75, -2.05, 0.0, 0.52, dict(top="soil", default="stone_trim"), skip=("bottom",))
    for x0, x1, y0, y1, z1 in ((2.90, 3.60, -3.55, -2.40, 0.96),
                               (3.66, 4.42, -3.60, -2.20, 1.24),
                               (4.48, 5.04, -3.45, -2.30, 1.06)):
        mb.box(x0, x1, y0, y1, 0.52, z1, "foliage", skip=("bottom",))


# Closed 20-vertex CCW polygon at ground level (left pilotis wing steps back to Y=PIL_D=1.90)
GROUND_OUTLINE = [
    (SE_X, PIL_D), (FS_X0, PIL_D), (FS_X0, FS_D), (FS_X1, FS_D), (FS_X1, 0.00),
] + OUTLINE[5:]


def _emit_wall(mb, x0, y0, x1, y1, z0, z1, region):
    if z1 - z0 > 1e-4:
        mb.rect([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], region)


def _wall_zones(x0, y0, x1, y1, z0, z1, stage):
    """Split a CCW perimeter edge into (ya/xb spans x vertical material zones) along the 20-vertex outline."""
    zp = zf(PALE_F)
    # SE center (-X) at X = SE_XOUT: dark vertical flanking columns [16.35..20.05] & [3.55..7.25]; middle cream
    # up to NF-4 and proud se_crown curtain module above NF-4
    if abs(x0 - SE_XOUT) < 1e-4 and abs(x1 - SE_XOUT) < 1e-4:
        g0, g1 = SE_GLASS
        yield (x0, y0, x1, g1, z0, z1, "stone")
        yield (x0, g1, x1, g0, z0, min(z1, zp), "stone")
        if z1 > zp:
            yield (x0, g1, x1, g0, max(z0, zp), min(z1, zf(NF - 4)), "pale")
        yield (x0, g0, x1, y1, z0, z1, "stone")
        return
    # Dark architectural slots, notch & SE recessed outer returns stay charcoal full height
    in_fslot = abs(x0 - FS_X0) < 1e-4 and abs(x1 - FS_X0) < 1e-4 or \
               abs(x0 - FS_X1) < 1e-4 and abs(x1 - FS_X1) < 1e-4 or \
               abs(y0 - FS_D) < 1e-4 and abs(y1 - FS_D) < 1e-4
    in_bslot = abs(x0 - BS_X0) < 1e-4 and abs(x1 - BS_X0) < 1e-4 or \
               abs(x0 - BS_X1) < 1e-4 and abs(x1 - BS_X1) < 1e-4 or \
               abs(y0 - (D - BS_D)) < 1e-4 and abs(y1 - (D - BS_D)) < 1e-4
    in_nwnotch_back = abs(x0 - NW_NIN) < 1e-4 and abs(x1 - NW_NIN) < 1e-4
    in_nwnotch_side = abs(y0 - NW_Y0) < 1e-4 and abs(y1 - NW_Y0) < 1e-4 or \
                      abs(y0 - NW_Y1) < 1e-4 and abs(y1 - NW_Y1) < 1e-4
    in_se_rec = abs(x0 - SE_X) < 1e-4 and abs(x1 - SE_X) < 1e-4 or \
                abs(y0 - SE_Y0) < 1e-4 and abs(y1 - SE_Y0) < 1e-4 or \
                abs(y0 - SE_Y1) < 1e-4 and abs(y1 - SE_Y1) < 1e-4
    if in_nwnotch_back:
        yield (x0, y0, x1, y1, z0, z1, "louver_back" if z0 >= GH - 1e-4 else "stone")
    elif in_fslot or in_bslot or in_nwnotch_side or in_se_rec:
        yield (x0, y0, x1, y1, z0, z1, "stone")
    else:
        if z0 < zp:
            yield (x0, y0, x1, y1, z0, min(z1, zp), "stone")
        if z1 > zp:
            yield (x0, y0, x1, y1, max(z0, zp), z1, "pale")


def parapet(mb, stage):
    """Non-overlapping 0.30 m parapet ring wrapping OUTLINE (SE_XOUT center owned by se_crown)."""
    t, ph = 0.30, H + 1.30
    segs = [
        (SE_X, SE_X + t, t, SE_Y0 + t),                       # SE front recess
        (SE_XOUT + 0.35, SE_X, SE_Y0, SE_Y0 + t),             # SE front project return (clears se_crown)
        (SE_XOUT + 0.35, SE_X, SE_Y1 - t, SE_Y1),             # SE back project return
        (SE_X, SE_X + t, SE_Y1 - t, D - t),                   # SE back recess
        (SE_X, FS_X0 - t, 0.0, t),                            # Front left wing
        (FS_X0 - t, FS_X0, 0.0, FS_D + t),                    # Front slot left
        (FS_X0, FS_X1, FS_D, FS_D + t),                       # Front slot back
        (FS_X1, FS_X1 + t, 0.0, FS_D + t),                    # Front slot right
        (FS_X1 + t, NW_X, 0.0, t),                            # Front right wing
        (NW_X - t, NW_X, t, NW_Y0),                           # NW front wing
        (NW_NIN - t, NW_X - t, NW_Y0 - t, NW_Y0),             # NW notch front side
        (NW_NIN - t, NW_NIN, NW_Y0, NW_Y1),                   # NW notch back
        (NW_NIN - t, NW_X - t, NW_Y1, NW_Y1 + t),             # NW notch rear side
        (NW_X - t, NW_X, NW_Y1, D - t),                       # NW back wing
        (BS_X1 + t, NW_X, D - t, D),                          # Back right wing
        (BS_X1, BS_X1 + t, D - BS_D - t, D),                  # Back slot right
        (BS_X0, BS_X1, D - BS_D - t, D - BS_D),               # Back slot back
        (BS_X0 - t, BS_X0, D - BS_D - t, D),                  # Back slot left
        (SE_X, BS_X0 - t, D - t, D),                          # Back left wing
    ]
    for x0, x1, y0, y1 in segs:
        mb.box(x0, x1, y0, y1, H, ph, "pale", skip=("bottom",))
    if stage == 0:
        for xc, yc in ((SE_X + 0.15, 0.15), (NW_X - 0.15, 0.15), (NW_X - 0.15, D - 0.15), (SE_X + 0.15, D - 0.15)):
            mb.box(xc - 0.12, xc + 0.12, yc - 0.12, yc + 0.12, ph, ph + 0.25, "obst_light", skip=("bottom",))


def build(stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    # Main tower envelope (GH..H) and recessed pilotis ground floor (0..GH) following the exact 20-vertex OSM polygon
    for i in range(len(OUTLINE)):
        (x0, y0), (x1, y1) = OUTLINE[i], OUTLINE[(i + 1) % len(OUTLINE)]
        for ax0, ay0, ax1, ay1, z0, z1, reg in _wall_zones(x0, y0, x1, y1, GH, H, stage):
            _emit_wall(mb, ax0, ay0, ax1, ay1, z0, z1, reg)
    for i in range(len(GROUND_OUTLINE)):
        (x0, y0), (x1, y1) = GROUND_OUTLINE[i], GROUND_OUTLINE[(i + 1) % len(GROUND_OUTLINE)]
        _emit_wall(mb, x0, y0, x1, y1, 0.0, GH, "stone")
    # Pilotis overhead soffit (bottom face at z=GH) and ground columns (open bay per user-03)
    mb.rect([(SE_X, PIL_D, GH), (FS_X0, PIL_D, GH), (FS_X0, 0.0, GH), (SE_X, 0.0, GH)], "stone")
    if stage < 2:
        mb.box(SE_X, SE_X + 1.20, 0.0, 1.20, 0, GH, "stone_trim", skip=("top", "bottom"))
        mb.box(-6.15, -5.45, 0.15, 0.85, 0, GH, "grey_stone", skip=("top", "bottom"))
    # Disjoint roof deck at z = H
    for x0, x1, y0, y1 in ROOF_RECTS:
        mb.rect([(x0, y0, H), (x1, y0, H), (x1, y1, H), (x0, y1, H)], "roof")
    if stage < 2:
        for f in range(1, NF + 1):
            if f == 2:
                ledges(mb, zf(f), 0.60, 0.55, f)
            elif f == NF:
                ledges(mb, H, 0.50, 0.35, f)
            else:
                ledges(mb, zf(f), LEDGE_P, LEDGE_T, f)
        parapet(mb, stage)
        # Floor 1 solid grey granite apron over left pilotis (user-03)
        mb.box(SE_X, FS_X0, -0.30, 0.0, zf(1) + LEDGE_T, zf(2), "grey_stone", skip=("back", "top", "bottom"))
    crown(mb, stage)
    entrance(mb, stage)
    if stage == 0:
        entrance_extras(mb)
    if stage < 2:
        terrace(mb, stage)
        ground_floor(mb, stage)
        for f in range(1, NF):
            floor_facade(mb, stage, f)
    return mb


main = build(0)
lod1 = build(1)
lod2 = build(2)

K.export_asset("HighriseTower103", 1, dict(main=main, lod1=lod1, lod2=lod2, windows=WS),
               A, K.out_dir_from_argv("output"), lot=(5, 4))
