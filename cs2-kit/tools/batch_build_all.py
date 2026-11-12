import os
import subprocess
import sys
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
VIEWER_PREVIEW_DIR = os.path.join(os.path.dirname(BASE_DIR), "asset-viewer", "public", "preview")

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


def build_dong_fbx(dong, copy_viewer=True):
    proj_dir = os.path.join(PROJECTS_DIR, f"exllu-{dong}")
    gen_file = os.path.join(proj_dir, f"exllu_{dong}_cs2.py")
    if not os.path.exists(gen_file):
        print(f"Generator {gen_file} not found!")
        return False

    print(f"\n==========================================")
    print(f" Building Exllu Tower {dong} FBX (Type {DONG_TYPES[dong]})")
    print(f"==========================================")

    out_dir = os.path.join(proj_dir, "output")
    # Run through tools/run_blender.py to guarantee FBX & blend export
    cmd = [sys.executable, os.path.join(BASE_DIR, "tools", "run_blender.py"), gen_file, "--", "--out", out_dir]
    r = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Build failed for {dong}:")
        print(r.stderr or r.stdout)
        return False
    print(f"Successfully exported FBX for HighriseTower{dong}")

    # Copy files to asset viewer preview
    if copy_viewer and os.path.exists(VIEWER_PREVIEW_DIR):
        asset_folder = os.path.join(out_dir, f"HighriseTower{dong}_L1_5x4")
        if os.path.exists(asset_folder):
            copied = 0
            for f in os.listdir(asset_folder):
                if f.endswith((".fbx", ".png")):
                    shutil.copy(os.path.join(asset_folder, f), os.path.join(VIEWER_PREVIEW_DIR, f))
                    copied += 1
            print(f"Copied {copied} files of {dong}동 to asset-viewer/public/preview/")

    return True


if __name__ == "__main__":
    target = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else sorted(list(DONG_TYPES.keys()))
    success = 0
    for d in target:
        if build_dong_fbx(d):
            success += 1
    print(f"\n==========================================")
    print(f" Batch build completed: {success}/{len(target)} towers exported successfully.")
    print(f"==========================================")
