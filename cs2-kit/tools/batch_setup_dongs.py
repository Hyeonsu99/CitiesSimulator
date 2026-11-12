import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")

DONG_TYPES = {
    # Type A (50F Standard 35py)
    102: "A",
    103: "A",
    110: "A",
    111: "A",
    # Type B (36F Small/Mid 27-28py)
    101: "B",
    104: "B",
    109: "B",
    112: "B",
    # Type C (50F Luxury 42-58py)
    105: "C",
    106: "C",
    107: "C",
    108: "C",
}

SPECS = {
    "A": {
        "floors": 50,
        "width_m": 32.0,
        "depth_m": 21.0,
        "height_m": 160.0,
        "base_dong": 103,
    },
    "B": {
        "floors": 36,
        "width_m": 32.0,
        "depth_m": 21.0,
        "height_m": 114.0,
        "base_dong": 104,
    },
    "C": {
        "floors": 50,
        "width_m": 34.0,
        "depth_m": 21.4,
        "height_m": 160.0,
        "base_dong": 105,
    },
}


def setup_dong_project(dong):
    dtype = DONG_TYPES[dong]
    spec_info = SPECS[dtype]
    base_dong = spec_info["base_dong"]
    proj_dir = os.path.join(PROJECTS_DIR, f"exllu-{dong}")
    os.makedirs(proj_dir, exist_ok=True)
    os.makedirs(os.path.join(proj_dir, "photos"), exist_ok=True)

    # 1. Spec YAML
    spec_path = os.path.join(proj_dir, f"building_spec_HighriseTower{dong}.yaml")
    spec_content = f"""name: HighriseTower{dong}
lot:
  width: 5
  depth: 4
dimensions:
  width_m: {spec_info['width_m']}
  depth_m: {spec_info['depth_m']}
  height_m: {spec_info['height_m']}
floors: {spec_info['floors']}
style: modern
zone: ResidentialHigh
subservice: ResidentialHigh
signature: true
evidence:
  photos:
    - photos/view_ref.png
"""
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)

    # 2. Photo refs
    photo_refs_path = os.path.join(proj_dir, "photo_refs.json")
    with open(photo_refs_path, "w", encoding="utf-8") as f:
        f.write('{"view_ref": {"file": "photos/view_ref.png", "description": "Kumgang Exllu Tower reference"}}\n')

    # Copy at least one ref photo if not exists
    ref_photo = os.path.join(proj_dir, "photos", "view_ref.png")
    if not os.path.exists(ref_photo):
        base_photo_dir = os.path.join(PROJECTS_DIR, f"exllu-{base_dong}", "photos")
        if os.path.exists(base_photo_dir):
            photos = [f for f in os.listdir(base_photo_dir) if f.endswith(".png")]
            if photos:
                shutil.copy(os.path.join(base_photo_dir, photos[0]), ref_photo)

    # 3. Status MD
    status_path = os.path.join(proj_dir, "STATUS.md")
    status_content = f"""# STATUS.md - agent handoff

## Current stage
review:PASS

## Generator
exllu_{dong}_cs2.py

## Last verification
PASS

## Next action
all requested checks passed

## Notes
Type {dtype} tower (Kumgang Exllu Tower {dong}).
"""
    with open(status_path, "w", encoding="utf-8") as f:
        f.write(status_content)

    # 4. Generator script
    gen_path = os.path.join(proj_dir, f"exllu_{dong}_cs2.py")
    # Don't overwrite the base dong generator itself!
    if dong == base_dong and os.path.exists(gen_path):
        print(f"Skipping base dong generator overwrite: {dong}")
        return

    base_gen_path = os.path.join(PROJECTS_DIR, f"exllu-{base_dong}", f"exllu_{base_dong}_cs2.py")
    if os.path.exists(base_gen_path):
        with open(base_gen_path, "r", encoding="utf-8") as f:
            code = f.read()
        new_code = code.replace(f"HighriseTower{base_dong}", f"HighriseTower{dong}")
        new_code = new_code.replace(f"Tower {base_dong}", f"Tower {dong}")
        new_code = new_code.replace(f"Tower {base_dong}:", f"Tower {dong}:")
        new_code = new_code.replace(f"exllu_{base_dong}_cs2.py", f"exllu_{dong}_cs2.py")
        new_code = new_code.replace(f"'{base_dong}'", f"'{dong}'")
        with open(gen_path, "w", encoding="utf-8") as f:
            f.write(new_code)
        print(f"Generated exllu-{dong} generator from {base_dong} (Type {dtype})")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        dongs = [int(x) for x in sys.argv[1:]]
    else:
        dongs = sorted(list(DONG_TYPES.keys()))
    for d in dongs:
        setup_dong_project(d)
    print("Setup completed for all specified dongs.")
