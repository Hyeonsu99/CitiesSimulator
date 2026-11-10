"""Fetch a Naver street-view cubemap (level L, 4x4 x 512 px per face) and render perspective views by compass yaw.

usage: python tools/naver_pano_view.py OUTDIR PANO_ID name:yaw:pitch:fov [...]
  yaw = compass degrees (0 = N, 90 = E), pitch = degrees up, fov = horizontal degrees.
  Tiles and metadata are cached in OUTDIR/<PANO_ID>/; views are saved as OUTDIR/<name>.png.

Why: the map.naver.com viewer swaps the requested pano for the newest nearby one and drifts its
heading, so URL pans are unreliable. Face 'f' of the cubemap looks along metadata camera_angle[1]
(checked against a known view). Find pano ids in the viewer URL (p=<id>) or the nearby API
/p/api/panorama/nearby/{lon}/{lat}/3 (needs a browser page context).
Output is evidence only: put crops in projects/<name>/photos/ and do not copy them into assets.
"""
import io, json, math, os, sys, urllib.request
import numpy as np
from PIL import Image

HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://map.naver.com/"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=30).read()


def faces(out, pid, n=4):
    d = os.path.join(out, pid); os.makedirs(d, exist_ok=True)
    meta_p = os.path.join(d, "meta.json")
    if not os.path.exists(meta_p):
        open(meta_p, "wb").write(get(f"https://panorama.map.naver.com/metadataV3/basic/{pid}?lang=ko"))
    meta = json.load(open(meta_p, encoding="utf-8"))
    F = {}
    for f in "frblud":
        p = os.path.join(d, f + ".png")
        if not os.path.exists(p):
            im = Image.new("RGB", (512 * n, 512 * n))
            for c in range(1, n + 1):
                for r in range(1, n + 1):
                    t = Image.open(io.BytesIO(get(f"https://panorama.pstatic.net/image/{pid}/512/L/{f}/{c}/{r}")))
                    im.paste(t.convert("RGB"), ((c - 1) * 512, (r - 1) * 512))
            im.save(p)
        F[f] = np.asarray(Image.open(p).convert("RGB"))
    return meta, F


def render(meta, F, yaw, pitch, fov, W=1600, H=1100):
    N = F["f"].shape[0]
    ly = math.radians(yaw - meta["camera_angle"][1]); pt = math.radians(pitch)
    fx = (W / 2) / math.tan(math.radians(fov) / 2)
    xs, ys = np.meshgrid(np.arange(W) - W / 2 + 0.5, np.arange(H) - H / 2 + 0.5)
    fw = np.array([math.sin(ly) * math.cos(pt), math.sin(pt), math.cos(ly) * math.cos(pt)])
    rt = np.array([math.cos(ly), 0.0, -math.sin(ly)])
    up = np.array([-math.sin(ly) * math.sin(pt), math.cos(pt), -math.cos(ly) * math.sin(pt)])
    d = fw[None, None] * fx + rt[None, None] * xs[..., None] - up[None, None] * ys[..., None]
    x, y, z = d[..., 0], d[..., 1], d[..., 2]
    ax, ay, az = np.abs(x), np.abs(y), np.abs(z)
    out = np.zeros((H, W, 3), np.uint8)
    sel = [("f", (az >= ax) & (az >= ay) & (z > 0), x / az, -y / az),
           ("b", (az >= ax) & (az >= ay) & (z <= 0), -x / az, -y / az),
           ("r", (ax > az) & (ax >= ay) & (x > 0), -z / ax, -y / ax),
           ("l", (ax > az) & (ax >= ay) & (x <= 0), z / ax, -y / ax),
           ("u", (ay > az) & (ay > ax) & (y > 0), x / ay, z / ay),
           ("d", (ay > az) & (ay > ax) & (y <= 0), x / ay, -z / ay)]
    for f, m, u, v in sel:
        px = np.clip(((u[m] + 1) / 2 * N).astype(int), 0, N - 1)
        py = np.clip(((v[m] + 1) / 2 * N).astype(int), 0, N - 1)
        out[m] = F[f][py, px]
    return Image.fromarray(out)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    out, pid = sys.argv[1], sys.argv[2]
    meta, F = faces(out, pid)
    print(pid, meta["info"]["photodate"], "cam", meta["camera_angle"], meta["longitude"], meta["latitude"])
    for spec in sys.argv[3:]:
        name, yaw, pitch, fov = spec.split(":")
        render(meta, F, float(yaw), float(pitch), float(fov)).save(os.path.join(out, name + ".png"))
        print("saved", name)
