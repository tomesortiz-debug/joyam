#!/usr/bin/env python3
"""Parse the exported .glb files back and render a contact-sheet preview.

Acts as both a structural validator (real GLB parsing, accessor reads,
skinning pose application) and a visual check. Optionally poses each rig
using a frame of one of its animation clips.
"""
import json, math, os, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "DarkMythicLegends")

CT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

def load_glb(path):
    with open(path, "rb") as f:
        magic, ver, _ = struct.unpack("<III", f.read(12))
        assert magic == 0x46546C67 and ver == 2, "bad GLB header"
        ln, ty = struct.unpack("<II", f.read(8))
        assert ty == 0x4E4F534A
        gltf = json.loads(f.read(ln))
        ln, ty = struct.unpack("<II", f.read(8))
        assert ty == 0x004E4942
        blob = f.read(ln)
    return gltf, blob

def read_acc(gltf, blob, i):
    a = gltf["accessors"][i]
    v = gltf["bufferViews"][a["bufferView"]]
    off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    n = a["count"] * NC[a["type"]]
    fmt = "<%d%s" % (n, CT[a["componentType"]])
    data = struct.unpack_from(fmt, blob, off)
    return np.array(data, dtype=np.float64).reshape(a["count"], NC[a["type"]])

def quat_mat(q):
    x, y, z, w = q
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

def pose_vertices(gltf, blob, clip=None, t=0.0):
    """Return (verts, normals, per-primitive (indices, color, emissive))."""
    nodes = gltf["nodes"]
    n_nodes = len(nodes)
    loc_t = [np.array(n.get("translation", [0, 0, 0]), float) for n in nodes]
    loc_r = [np.array(n.get("rotation", [0, 0, 0, 1]), float) for n in nodes]
    if clip is not None:
        anim = next(a for a in gltf["animations"] if a["name"] == clip)
        for ch in anim["channels"]:
            sm = anim["samplers"][ch["sampler"]]
            times = read_acc(gltf, blob, sm["input"]).ravel()
            vals = read_acc(gltf, blob, sm["output"])
            k = np.clip(np.searchsorted(times, t), 1, len(times)-1)
            f = (t - times[k-1]) / max(1e-9, times[k] - times[k-1])
            val = vals[k-1] * (1-f) + vals[k] * f
            tgt = ch["target"]
            if tgt["path"] == "rotation":
                loc_r[tgt["node"]] = val / np.linalg.norm(val)
            elif tgt["path"] == "translation":
                loc_t[tgt["node"]] = val
    # globals
    parent = [-1] * n_nodes
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i
    world = [None] * n_nodes
    def gw(i):
        if world[i] is not None: return world[i]
        m = np.eye(4)
        m[:3, :3] = quat_mat(loc_r[i]); m[:3, 3] = loc_t[i]
        world[i] = m if parent[i] < 0 else gw(parent[i]) @ m
        return world[i]
    for i in range(n_nodes): gw(i)

    skin = gltf["skins"][0]
    ibms = read_acc(gltf, blob, skin["inverseBindMatrices"]).reshape(-1, 4, 4)
    jmats = [gw(j) @ ibms[k].T for k, j in enumerate(skin["joints"])]

    mesh = gltf["meshes"][0]
    p0 = mesh["primitives"][0]["attributes"]
    pos = read_acc(gltf, blob, p0["POSITION"])
    nrm = read_acc(gltf, blob, p0["NORMAL"])
    jnt = read_acc(gltf, blob, p0["JOINTS_0"]).astype(int)[:, 0]
    out_p = np.empty_like(pos); out_n = np.empty_like(nrm)
    for k in range(len(jmats)):
        sel = jnt == k
        if not sel.any(): continue
        m = jmats[k]
        out_p[sel] = pos[sel] @ m[:3, :3].T + m[:3, 3]
        out_n[sel] = nrm[sel] @ m[:3, :3].T
    prims = []
    for pr in mesh["primitives"]:
        idx = read_acc(gltf, blob, pr["indices"]).astype(int).ravel()
        mat = gltf["materials"][pr["material"]]
        em = np.array(mat.get("emissiveFactor", [0, 0, 0]))
        col = np.array(mat["pbrMetallicRoughness"]["baseColorFactor"][:3])
        prims.append((idx, col, em))
    return out_p, out_n, prims

def render(gltf, blob, size=420, clip=None, t=0.0, yaw=28.0, bg=None):
    verts, norms, prims = pose_vertices(gltf, blob, clip, t)
    ya, pa = math.radians(yaw), math.radians(-12)
    Ry = np.array([[math.cos(ya), 0, math.sin(ya)], [0, 1, 0], [-math.sin(ya), 0, math.cos(ya)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(pa), -math.sin(pa)], [0, math.sin(pa), math.cos(pa)]])
    R = Rx @ Ry
    v = verts @ R.T
    n = norms @ R.T
    span = 2.6
    cx, cy = size/2, size*0.94
    scale = size / span
    img = Image.new("RGB", (size, size), bg or (24, 26, 34))
    dr = ImageDraw.Draw(img)
    light = np.array([0.45, 0.75, 0.55]); light /= np.linalg.norm(light)
    tris = []
    for idx, col, em in prims:
        for i in range(0, len(idx), 3):
            a, b, c = idx[i], idx[i+1], idx[i+2]
            z = (v[a, 2] + v[b, 2] + v[c, 2]) / 3
            tris.append((z, (a, b, c), col, em))
    tris.sort(key=lambda x: x[0])
    for z, (a, b, c), col, em in tris:
        fn = n[a]
        if fn[2] < -0.01: continue
        sh = 0.38 + 0.62 * max(0.0, float(fn @ light))
        rgb = np.clip(col * sh + em * 1.1, 0, 1)
        pts = [(cx + v[k, 0]*scale, cy - v[k, 1]*scale) for k in (a, b, c)]
        dr.polygon(pts, fill=tuple(int(q*255) for q in rgb))
    return img

def main():
    files = sorted(os.listdir(os.path.join(PACK, "GLB")))
    files = [f for f in files if f.endswith(".glb")]
    # order by roster order embedded in scene name? keep alphabetical is fine;
    # but prefer roster order from generator for a nicer sheet:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from generate_pack import ROSTER
    order = [n.replace(" ", "") + ".glb" for n, _, _ in ROSTER]
    files = [f for f in order if f in files]
    cols, rows, cell = 5, 4, 420
    label_h = 34
    sheet = Image.new("RGB", (cols*cell, rows*(cell+label_h)), (17, 18, 24))
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(20)
    except TypeError:
        font = ImageFont.load_default()
    clip = sys.argv[1] if len(sys.argv) > 1 else None
    t = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    for i, f in enumerate(files):
        gltf, blob = load_glb(os.path.join(PACK, "GLB", f))
        names = [a["name"] for a in gltf.get("animations", [])]
        assert names == ["Idle", "Walk", "Attack"], f + " clips: " + str(names)
        img = render(gltf, blob, cell, clip, t)
        r, c = divmod(i, cols)
        sheet.paste(img, (c*cell, r*(cell+label_h)))
        name = gltf["scenes"][0]["name"]
        dr.text((c*cell + cell/2, r*(cell+label_h) + cell + 6), name.upper(),
                fill=(230, 228, 240), font=font, anchor="ma")
    out = os.path.join(PACK, "preview.png")
    sheet.save(out)
    print("validated %d glb files, wrote %s" % (len(files), out))

if __name__ == "__main__":
    main()
