"""Data-driven mixed-use/school example using generic volumes and wall features."""
import json
import math
import os
import sys


def find_kit():
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        if os.path.exists(os.path.join(path, "cs2kit.py")):
            return path
        path = os.path.dirname(path)
    raise RuntimeError("cs2kit.py not found")


sys.path.insert(0, find_kit())
import cs2kit as K  # noqa: E402

spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generic_spec.json")
with open(spec_path, encoding="utf-8") as f:
    spec = json.load(f)

A = K.Atlas(size=4096, pad=16)
materials = {
    "wall": ((210, 211, 204), 0.0, 0.35),
    "base_stone": ((78, 79, 81), 0.0, 0.3),
    "heli_green": ((82, 142, 113), 0.0, 0.25),
    "heli_white": ((224, 226, 213), 0.0, 0.25),
    "roof": ((105, 108, 110), 0.0, 0.35),
    "frame": ((105, 112, 118), 0.65, 0.55),
    "sign_slot": ((82, 88, 92), 0.0, 0.35),
    "louver_back": ((45, 48, 50), 0.0, 0.3),
    "louver": ((115, 119, 120), 0.6, 0.5),
    "railing": ((115, 120, 123), 0.65, 0.5),
    "glass": ((135, 165, 180), 0.0, 0.8),
    "canopy": ((160, 163, 162), 0.2, 0.45),
    "pier_pink": ((176, 140, 130), 0.0, 0.4),
    "roof_equipment": ((125, 128, 129), 0.3, 0.4),
}
for name, (color, metal, gloss) in materials.items():
    A.add(name, color=color, ctrl=(0, 0, 0), metal=metal, gloss=gloss, px=128)

main = K.build_volume_spec(A, spec, K.QualityStage.FULL)
lod1 = K.build_volume_spec(A, spec, K.QualityStage.SIMPLIFY_TRIM)
lod2 = K.build_volume_spec(A, spec, K.QualityStage.LOD_CULL)
# 103 rooftop: a raised square helipad, as visible in the supplied overhead image.
# Dimensions and the tower footprint remain estimated until scaled site plans are available.
for obj, stage in ((main, 0), (lod1, 1), (lod2, 2)):
    mb, meta = obj["mb"], obj["meta"]
    for wall in ("tower:front_left", "tower:front_right", "tower:front_center", "tower:right", "tower:left", "tower:back"):
        K.feature_panel(meta, wall, 0.0, 1.0, 0.1, 19.0, "base_stone", 0.012)
    # Outer front bays are dark stone full height (user-02/05); split ratio estimated.
    K.feature_panel(meta, "tower:front_left", 0.0, 0.6, 19.0, 147.0, "base_stone", 0.012)
    K.feature_panel(meta, "tower:front_right", 0.4, 1.0, 19.0, 147.0, "base_stone", 0.012)
    mb.box(-8,8,3,19,147,148.2,"wall",skip=("bottom",))
    mb.box(-6.6,6.6,4.4,17.6,148.2,148.25,"heli_green",skip=("bottom",))
    # Entrance portal (user-03): dark canopy frame, dark left pier, pink granite right pier, stair.
    # Canopy stops 1.6 m off the wall so the floor-1 windows behind it stay unblocked.
    mb.box(7.5,15.4,-4,-1.6,4.4,5.2,"base_stone")
    mb.box(7.5,8.5,-4,-3,0,4.4,"base_stone",skip=("bottom","top"))
    mb.box(14.0,15.5,-4.4,-2.6,0,5.4,"pier_pink",skip=("bottom",))
    if stage < 2:
        for x0,x1,y0,y1 in [(-6.1,-5.95,4.9,17.1),(5.95,6.1,4.9,17.1),(-5.95,5.95,4.9,5.05),(-5.95,5.95,16.95,17.1),(-1.7,-1.4,8.7,13.3),(1.4,1.7,8.7,13.3),(-1.4,1.4,10.85,11.15)]:
            mb.box(x0,x1,y0,y1,148.25,148.29,"heli_white",skip=("bottom",))
        for i in range(32):
            a,b=2*math.pi*i/32,2*math.pi*(i+1)/32
            mb.rect([(r*math.cos(t),11+r*math.sin(t),148.30) for r,t in ((4.0,a),(4.0,b),(3.86,b),(3.86,a))],"heli_white")
        # Entrance volume: position and depth are estimated from the 103 close-up.
        mb.box(8.6,13.9,-1.75,-1.6,0.6,4.4,{"front":"glass","default":"base_stone"},skip=("bottom",))
        for i in range(4):  # treads: separate y slices, only the riser and top are exposed
            mb.box(8.6,13.9,-3.75+i*0.5,-3.25+i*0.5 if i<3 else -1.75,0,0.15*(i+1),"canopy",skip=("bottom","back"))
        if stage == 0:
            for floor in range(2,50):
                z=floor*2.94
                for x0,x1 in ((-16,-5.5),(5.5,16)):
                    mb.box(x0,x1,-.45,0,z,z+.12,"wall")

K.export_asset("GeumgangExlluTower", 1,
               dict(main=main["mb"], lod1=lod1["mb"], lod2=lod2["mb"],
                    gls=main["gls"], lod1_gls=lod1["gls"], windows=main["windows"]),
               A, K.out_dir_from_argv("output"), metadata=main["metadata"])
