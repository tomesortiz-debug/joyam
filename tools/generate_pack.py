#!/usr/bin/env python3
"""DARK MYTHIC LEGENDS — 20-monster low-poly character pack generator.

Procedurally builds 20 rigged, skinned, animated low-poly monsters and
exports each as a self-contained .glb (glTF 2.0 binary) ready for Unity
(via glTFast / UnityGLTF) or any glTF-capable engine.

Every rig shares the same 11-joint skeleton and exactly three baked
animation clips: Idle, Walk, Attack.
"""
import json, math, os, struct, zipfile

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DarkMythicLegends")

# ---------------------------------------------------------------- skeleton --
JOINT_NAMES = ["Root", "Hips", "Chest", "Head", "ArmL", "ArmR",
               "LegL", "LegR", "Tail", "WingL", "WingR"]
J = {n: i for i, n in enumerate(JOINT_NAMES)}
PARENT = {"Root": None, "Hips": "Root", "Chest": "Hips", "Head": "Chest",
          "ArmL": "Chest", "ArmR": "Chest", "LegL": "Hips", "LegR": "Hips",
          "Tail": "Hips", "WingL": "Chest", "WingR": "Chest"}

# ------------------------------------------------------------------- maths --
def quat_from_euler(rx, ry, rz):
    """Euler degrees (X, then Y, then Z) -> quaternion (x, y, z, w)."""
    def axis_q(ax, deg):
        h = math.radians(deg) / 2.0
        s = math.sin(h)
        return (ax[0]*s, ax[1]*s, ax[2]*s, math.cos(h))
    def mul(a, b):
        ax, ay, az, aw = a; bx, by, bz, bw = b
        return (aw*bx + ax*bw + ay*bz - az*by,
                aw*by - ax*bz + ay*bw + az*bx,
                aw*bz + ax*by - ay*bx + az*bw,
                aw*bw - ax*bx - ay*by - az*bz)
    q = mul(axis_q((0, 0, 1), rz), mul(axis_q((0, 1, 0), ry), axis_q((1, 0, 0), rx)))
    n = math.sqrt(sum(c*c for c in q))
    return tuple(c/n for c in q)

# -------------------------------------------------------------- box meshes --
# (normal, u-axis, v-axis) per face, chosen so u x v == normal (CCW winding).
_FACES = [((1,0,0),(0,1,0),(0,0,1)), ((-1,0,0),(0,0,1),(0,1,0)),
          ((0,1,0),(0,0,1),(1,0,0)), ((0,-1,0),(1,0,0),(0,0,1)),
          ((0,0,1),(1,0,0),(0,1,0)), ((0,0,-1),(0,1,0),(1,0,0))]

def add_box(geo, joint, center, size, color, emissive=False):
    """Append an axis-aligned box bound rigidly to one joint."""
    cx, cy, cz = center
    hx, hy, hz = size[0]/2.0, size[1]/2.0, size[2]/2.0
    key = (tuple(round(c, 4) for c in color), bool(emissive))
    grp = geo["groups"].setdefault(key, [])
    for n, u, v in _FACES:
        hu = abs(u[0])*hx + abs(u[1])*hy + abs(u[2])*hz
        hv = abs(v[0])*hx + abs(v[1])*hy + abs(v[2])*hz
        hn = abs(n[0])*hx + abs(n[1])*hy + abs(n[2])*hz
        base = len(geo["pos"])
        fc = (cx + n[0]*hn, cy + n[1]*hn, cz + n[2]*hn)
        for su, sv in ((-1,-1), (1,-1), (1,1), (-1,1)):
            geo["pos"].append((fc[0] + su*u[0]*hu + sv*v[0]*hv,
                               fc[1] + su*u[1]*hu + sv*v[1]*hv,
                               fc[2] + su*u[2]*hu + sv*v[2]*hv))
            geo["nrm"].append(n)
            geo["joint"].append(joint)
        grp += [base, base+1, base+2, base, base+2, base+3]

def new_geo():
    return {"pos": [], "nrm": [], "joint": [], "groups": {}}

# --------------------------------------------------------- character build --
def hexc(h, mul=1.0):
    h = h.lstrip("#")
    return tuple(min(1.0, int(h[i:i+2], 16)/255.0*mul) for i in (0, 2, 4))

def build_character(spec):
    """Return (geo, joint_global_positions) for one monster spec."""
    s = spec.get("scale", 1.0)
    bulk = spec.get("bulk", 1.0)
    leg_h = 0.62 * s
    torso = 0.68 * s
    head_h = 0.34 * s * spec.get("head", 1.0)
    w = 0.44 * s * bulk
    d = 0.26 * s * bulk
    hip_y = leg_h
    sh_y = hip_y + torso * 0.92
    head_base = hip_y + torso
    aw = 0.13 * s * bulk
    arm_len = 0.52 * s
    lw = 0.15 * s * bulk
    lx = w * 0.30

    g = {"Root": (0, 0, 0), "Hips": (0, hip_y, 0),
         "Chest": (0, hip_y + torso*0.45, 0), "Head": (0, head_base, 0),
         "ArmL": ( (w/2 + aw/2)*1.02, sh_y, 0), "ArmR": (-(w/2 + aw/2)*1.02, sh_y, 0),
         "LegL": (lx, hip_y, 0), "LegR": (-lx, hip_y, 0),
         "Tail": (0, hip_y + torso*0.1, -d/2),
         "WingL": ( w*0.30, sh_y - 0.02, -d/2), "WingR": (-w*0.30, sh_y - 0.02, -d/2)}

    P = spec["palette"]
    pri, sec, dark, glow = hexc(P[0]), hexc(P[1]), hexc(P[2]), hexc(P[3])
    geo = new_geo()
    B = lambda j, c, sz, col, em=False: add_box(geo, J[j], c, sz, col, em)

    # torso
    B("Hips", (0, hip_y + torso*0.14, 0), (w*0.92, torso*0.32, d*0.95), sec)
    B("Hips", (0, hip_y + torso*0.02, 0.01), (w*0.98, torso*0.10, d*1.02), dark)   # belt
    B("Chest", (0, hip_y + torso*0.63, 0), (w, torso*0.52, d*1.05), pri)
    if spec.get("emblem", True):
        B("Chest", (0, hip_y + torso*0.66, d*0.55), (w*0.28, torso*0.2, 0.02*s), glow, True)
    if spec.get("pads"):
        for sx in (1, -1):
            B("Chest", (sx*(w/2 + aw*0.4), sh_y + 0.05*s, 0), (aw*2.0, 0.10*s, d*1.1), dark)
    if spec.get("spikes"):
        for i in range(3):
            y = hip_y + torso*(0.35 + 0.22*i)
            sz = 0.085*s*(1.0 - 0.2*i)
            B("Chest", (0, y, -d*0.62 - sz*0.4), (sz, sz*1.6, sz), dark)

    # head
    hw, hd = 0.30*s*spec.get("head_w", 1.0), 0.26*s
    hy = head_base + head_h*0.55
    B("Head", (0, hy, 0), (hw, head_h, hd), pri)
    if spec.get("hood"):
        B("Head", (0, hy + head_h*0.12, -hd*0.12), (hw*1.25, head_h*1.15, hd*1.15), dark)
    # eyes
    n_eyes = spec.get("eyes", 2)
    ez = hd/2 + (hd*0.14 if spec.get("hood") else 0.005*s)
    es = 0.055*s
    if n_eyes == 1:
        B("Head", (0, hy + head_h*0.1, ez), (es*1.9, es, 0.02*s), glow, True)
    else:
        xs = [hw*0.24, -hw*0.24] + ([0.0] if n_eyes == 3 else [])
        for i, ex in enumerate(xs):
            ey = hy + head_h*(0.28 if i == 2 else 0.1)
            B("Head", (ex, ey, ez), (es, es*1.25, 0.02*s), glow, True)
    if spec.get("snout"):
        B("Head", (0, hy - head_h*0.18, hd/2 + 0.07*s), (hw*0.55, head_h*0.4, 0.15*s), sec)
        B("Head", (0, hy - head_h*0.33, hd/2 + 0.13*s), (hw*0.4, head_h*0.12, 0.05*s), dark)
    if spec.get("tusks"):
        for sx in (1, -1):
            B("Head", (sx*hw*0.3, hy - head_h*0.42, hd/2 + 0.02*s), (0.05*s, 0.14*s, 0.05*s), sec)
    horns = spec.get("horns", "none")
    top = hy + head_h/2
    if horns == "up":
        for sx in (1, -1):
            B("Head", (sx*hw*0.3, top + 0.07*s, 0), (0.07*s, 0.16*s, 0.07*s), sec)
            B("Head", (sx*hw*0.3, top + 0.17*s, 0), (0.045*s, 0.10*s, 0.045*s), sec)
    elif horns == "curved":
        for sx in (1, -1):
            B("Head", (sx*hw*0.42, top + 0.05*s, 0), (0.08*s, 0.12*s, 0.08*s), sec)
            B("Head", (sx*hw*0.52, top + 0.13*s, 0.03*s), (0.055*s, 0.10*s, 0.055*s), sec)
            B("Head", (sx*hw*0.56, top + 0.19*s, 0.08*s), (0.04*s, 0.055*s, 0.06*s), sec)
    elif horns == "side":
        for sx in (1, -1):
            B("Head", (sx*(hw*0.62), hy + head_h*0.25, 0), (0.14*s, 0.075*s, 0.075*s), sec)
            B("Head", (sx*(hw*0.62 + 0.09*s), hy + head_h*0.42, 0), (0.055*s, 0.11*s, 0.055*s), sec)
    elif horns == "single":
        B("Head", (0, top + 0.09*s, 0.02*s), (0.06*s, 0.2*s, 0.06*s), glow, True)
    elif horns == "crown":
        B("Head", (0, top + 0.035*s, 0), (hw*1.05, 0.06*s, hd*1.05), sec)
        for ex in (hw*0.35, 0, -hw*0.35):
            B("Head", (ex, top + 0.11*s, 0), (0.05*s, 0.09*s, 0.05*s), sec)
        B("Head", (0, top + 0.10*s, hd*0.45), (0.05*s, 0.05*s, 0.03*s), glow, True)
    if spec.get("ears"):
        for sx in (1, -1):
            B("Head", (sx*hw*0.42, top + 0.05*s, -0.02*s), (0.06*s, 0.14*s, 0.05*s), pri)

    # arms + fists (+ claws / weapon)
    for side, jn in ((1, "ArmL"), (-1, "ArmR")):
        ax = g[jn][0]
        B(jn, (ax, sh_y - arm_len*0.42, 0), (aw, arm_len*0.8, aw), pri)
        B(jn, (ax, sh_y - arm_len*0.92, 0), (aw*1.25, arm_len*0.22, aw*1.25), sec)
        if spec.get("claws"):
            for k in (-1, 0, 1):
                B(jn, (ax + k*aw*0.4, sh_y - arm_len*1.05, aw*0.35), (0.03*s, 0.07*s, 0.05*s), dark)
    wep = spec.get("weapon", "none")
    if wep != "none":
        hx, hy_, hz = g["ArmR"][0], sh_y - arm_len*0.95, aw*0.9
        if wep == "staff":
            B("ArmR", (hx, hy_ + 0.15*s, hz), (0.05*s, 1.15*s, 0.05*s), dark)
            B("ArmR", (hx, hy_ + 0.78*s, hz), (0.11*s, 0.11*s, 0.11*s), glow, True)
        elif wep == "sword":
            B("ArmR", (hx, hy_ - 0.02*s, hz), (0.05*s, 0.16*s, 0.05*s), dark)
            B("ArmR", (hx, hy_ + 0.09*s, hz), (0.16*s, 0.035*s, 0.05*s), sec)
            B("ArmR", (hx, hy_ + 0.44*s, hz), (0.07*s, 0.66*s, 0.025*s), sec)
            B("ArmR", (hx, hy_ + 0.44*s, hz), (0.025*s, 0.6*s, 0.028*s), glow, True)
        elif wep == "axe":
            B("ArmR", (hx, hy_ + 0.18*s, hz), (0.055*s, 0.95*s, 0.055*s), dark)
            B("ArmR", (hx + 0.10*s, hy_ + 0.52*s, hz), (0.17*s, 0.24*s, 0.045*s), sec)
            B("ArmR", (hx + 0.19*s, hy_ + 0.52*s, hz), (0.035*s, 0.3*s, 0.05*s), sec)
        elif wep == "club":
            B("ArmR", (hx, hy_ + 0.1*s, hz), (0.07*s, 0.6*s, 0.07*s), dark)
            B("ArmR", (hx, hy_ + 0.48*s, hz), (0.16*s, 0.28*s, 0.16*s), sec)
            for k in (-1, 1):
                B("ArmR", (hx + k*0.1*s, hy_ + 0.52*s, hz), (0.05*s, 0.06*s, 0.05*s), dark)
        elif wep == "scythe":
            B("ArmR", (hx, hy_ + 0.25*s, hz), (0.05*s, 1.25*s, 0.05*s), dark)
            B("ArmR", (hx + 0.16*s, hy_ + 0.84*s, hz), (0.36*s, 0.06*s, 0.04*s), sec)
            B("ArmR", (hx + 0.33*s, hy_ + 0.70*s, hz), (0.05*s, 0.24*s, 0.04*s), glow, True)
        elif wep == "trident":
            B("ArmR", (hx, hy_ + 0.2*s, hz), (0.05*s, 1.05*s, 0.05*s), dark)
            B("ArmR", (hx, hy_ + 0.74*s, hz), (0.24*s, 0.05*s, 0.05*s), sec)
            for ex in (-0.095, 0.0, 0.095):
                B("ArmR", (hx + ex*s, hy_ + 0.85*s, hz), (0.04*s, 0.18*s, 0.04*s), glow, True)

    # legs + feet
    for side, jn in ((1, "LegL"), (-1, "LegR")):
        xx = g[jn][0]
        B(jn, (xx, hip_y*0.55, 0), (lw, leg_h*0.88, lw), sec)
        B(jn, (xx, 0.06*s, 0.03*s), (lw*1.15, 0.12*s, lw*1.7), dark)

    # tail
    if spec.get("tail"):
        ty = g["Tail"][1]
        B("Tail", (0, ty - 0.04*s, -d/2 - 0.14*s), (0.10*s, 0.10*s, 0.30*s), pri)
        B("Tail", (0, ty - 0.10*s, -d/2 - 0.40*s), (0.07*s, 0.07*s, 0.26*s), sec)
        B("Tail", (0, ty - 0.13*s, -d/2 - 0.58*s), (0.05*s, 0.09*s, 0.10*s), glow,
          spec.get("tail_glow", False))

    # wings
    if spec.get("wings"):
        ws = spec.get("wing_size", 1.0)
        for sx, jn in ((1, "WingL"), (-1, "WingR")):
            wx = g[jn][0]
            B(jn, (wx + sx*0.22*s*ws, sh_y + 0.10*s*ws, -d/2 - 0.05*s), (0.42*s*ws, 0.07*s, 0.05*s), dark)
            B(jn, (wx + sx*0.40*s*ws, sh_y - 0.06*s*ws, -d/2 - 0.05*s), (0.30*s*ws, 0.26*s*ws, 0.035*s), sec)
            B(jn, (wx + sx*0.47*s*ws, sh_y + 0.16*s*ws, -d/2 - 0.05*s), (0.06*s, 0.22*s*ws, 0.035*s), sec)
    return geo, g

# -------------------------------------------------------------- animations --
def clip_curves(name, spec):
    """Return (duration, fn(t) -> (rot_deg per joint, hips_dy))."""
    s2 = math.pi * 2
    has_tail, has_wings = spec.get("tail", False), bool(spec.get("wings"))
    def idle(t):
        p = s2 * t / 2.0
        r = {"Chest": (2.5*math.sin(p), 0, 0), "Head": (0, 6*math.sin(p + 0.7), 0),
             "ArmL": (4*math.sin(p), 0, -3 + 2*math.sin(p)),
             "ArmR": (4*math.sin(p + 0.3), 0, 3 - 2*math.sin(p))}
        if has_tail:  r["Tail"] = (0, 14*math.sin(p*1.5), 0)
        if has_wings:
            f = 12*math.sin(p)
            r["WingL"] = (0, 0, f); r["WingR"] = (0, 0, -f)
        return r, 0.022*math.sin(p*2)
    def walk(t):
        p = s2 * t / 1.0
        sw = math.sin(p)
        r = {"LegL": (32*sw, 0, 0), "LegR": (-32*sw, 0, 0),
             "ArmL": (-26*sw, 0, -4), "ArmR": (26*sw, 0, 4),
             "Chest": (4, 6*sw, 0), "Head": (-3, -4*sw, 0)}
        if has_tail:  r["Tail"] = (6, 18*math.sin(p*2 + 1), 0)
        if has_wings:
            f = 18*math.sin(p*2)
            r["WingL"] = (0, 0, 8 + f); r["WingR"] = (0, 0, -8 - f)
        return r, 0.03*abs(math.cos(p))
    def attack(t):
        d = 0.9
        u = t / d
        def env(a, b, x):  # 0..1 ramp between phase a..b, smoothstep
            if x <= a: return 0.0
            if x >= b: return 1.0
            k = (x - a) / (b - a)
            return k*k*(3 - 2*k)
        raise_amt = env(0.0, 0.35, u) * (1 - env(0.42, 0.62, u))
        slam_amt = env(0.42, 0.62, u) * (1 - env(0.75, 1.0, u))
        arm_x = -155*raise_amt - 55*slam_amt
        lean = -8*raise_amt + 16*slam_amt
        r = {"ArmR": (arm_x, 0, 8*raise_amt), "ArmL": (18*slam_amt - 10*raise_amt, 0, -6),
             "Chest": (lean, -10*raise_amt + 8*slam_amt, 0),
             "Head": (-lean*0.5, 0, 0),
             "LegL": (10*slam_amt, 0, 0), "LegR": (-8*slam_amt, 0, 0)}
        if has_tail:  r["Tail"] = (0, 25*math.sin(s2*u), 0)
        if has_wings:
            f = 20*raise_amt - 10*slam_amt
            r["WingL"] = (0, 0, f); r["WingR"] = (0, 0, -f)
        return r, -0.05*slam_amt
    return {"Idle": (2.0, idle), "Walk": (1.0, walk), "Attack": (0.9, attack)}[name]

# -------------------------------------------------------------- glb writer --
class GLB:
    def __init__(self):
        self.blob = bytearray()
        self.views, self.accessors = [], []

    def _view(self, data, target=None):
        while len(self.blob) % 4:
            self.blob.append(0)
        off = len(self.blob)
        self.blob += data
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target: v["target"] = target
        self.views.append(v)
        return len(self.views) - 1

    def acc(self, fmt, comp, atype, data, target=None, minmax=False, norm=False):
        flat = [c for item in data for c in (item if isinstance(item, (tuple, list)) else (item,))]
        raw = struct.pack("<%d%s" % (len(flat), fmt), *flat)
        a = {"bufferView": self._view(raw, target), "componentType": comp,
             "count": len(data), "type": atype}
        if norm: a["normalized"] = True
        if minmax:
            n = len(data[0]) if isinstance(data[0], (tuple, list)) else 1
            if n == 1:
                a["min"], a["max"] = [min(data)], [max(data)]
            else:
                a["min"] = [min(v[i] for v in data) for i in range(n)]
                a["max"] = [max(v[i] for v in data) for i in range(n)]
        self.accessors.append(a)
        return len(self.accessors) - 1

def export_glb(path, name, spec):
    geo, g = build_character(spec)
    glb = GLB()
    ARRAY, ELEM, FLOAT, USHORT, UBYTE = 34962, 34963, 5126, 5123, 5121

    a_pos = glb.acc("f", FLOAT, "VEC3", geo["pos"], ARRAY, minmax=True)
    a_nrm = glb.acc("f", FLOAT, "VEC3", geo["nrm"], ARRAY)
    a_jnt = glb.acc("B", UBYTE, "VEC4", [(j, 0, 0, 0) for j in geo["joint"]], ARRAY)
    a_wgt = glb.acc("f", FLOAT, "VEC4", [(1.0, 0.0, 0.0, 0.0)] * len(geo["joint"]), ARRAY)

    materials, prims = [], []
    for (color, emissive), idx in geo["groups"].items():
        mi = len(materials)
        mat = {"name": "M%d" % mi, "doubleSided": False,
               "pbrMetallicRoughness": {"baseColorFactor": [*color, 1.0],
                                        "metallicFactor": 0.1, "roughnessFactor": 0.75}}
        if emissive:
            mat["pbrMetallicRoughness"]["baseColorFactor"] = [color[0]*0.55, color[1]*0.55, color[2]*0.55, 1.0]
            mat["emissiveFactor"] = list(color)
        materials.append(mat)
        a_idx = glb.acc("H", USHORT, "SCALAR", idx, ELEM)
        prims.append({"attributes": {"POSITION": a_pos, "NORMAL": a_nrm,
                                     "JOINTS_0": a_jnt, "WEIGHTS_0": a_wgt},
                      "indices": a_idx, "material": mi})

    # nodes: joints 0..10 then mesh node 11
    nodes = []
    for jn in JOINT_NAMES:
        p = PARENT[jn]
        loc = g[jn] if p is None else tuple(g[jn][i] - g[p][i] for i in range(3))
        node = {"name": jn, "translation": list(loc)}
        kids = [J[c] for c, par in PARENT.items() if par == jn]
        if kids: node["children"] = kids
        nodes.append(node)
    mesh_node = len(nodes)
    nodes.append({"name": name.replace(" ", ""), "mesh": 0, "skin": 0})

    ibm = []
    for jn in JOINT_NAMES:
        x, y, z = g[jn]
        ibm.append((1,0,0,0, 0,1,0,0, 0,0,1,0, -x,-y,-z,1))
    a_ibm = glb.acc("f", FLOAT, "MAT4", ibm)

    # animations
    animations = []
    fps = 15
    for clip in ("Idle", "Walk", "Attack"):
        dur, fn = clip_curves(clip, spec)
        nfr = max(2, int(round(dur * fps))) + 1
        times = [dur * i / (nfr - 1) for i in range(nfr)]
        rot_keys = {jn: [] for jn in JOINT_NAMES}
        hip_keys = []
        for t in times:
            rots, dy = fn(t)
            for jn in JOINT_NAMES:
                rot_keys[jn].append(quat_from_euler(*rots.get(jn, (0, 0, 0))))
            hip_keys.append((g["Hips"][0], g["Hips"][1] + dy, g["Hips"][2]))
        a_time = glb.acc("f", FLOAT, "SCALAR", times, minmax=True)
        samplers, channels = [], []
        for jn in JOINT_NAMES:
            if all(abs(q[3] - 1.0) < 1e-6 for q in rot_keys[jn]):
                continue
            a_out = glb.acc("f", FLOAT, "VEC4", rot_keys[jn])
            samplers.append({"input": a_time, "output": a_out, "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers)-1,
                             "target": {"node": J[jn], "path": "rotation"}})
        a_tr = glb.acc("f", FLOAT, "VEC3", hip_keys)
        samplers.append({"input": a_time, "output": a_tr, "interpolation": "LINEAR"})
        channels.append({"sampler": len(samplers)-1,
                         "target": {"node": J["Hips"], "path": "translation"}})
        animations.append({"name": clip, "samplers": samplers, "channels": channels})

    gltf = {"asset": {"version": "2.0", "generator": "DarkMythicLegends generator",
                      "copyright": "CC0 - generated character pack"},
            "scene": 0,
            "scenes": [{"name": name, "nodes": [J["Root"], mesh_node]}],
            "nodes": nodes,
            "meshes": [{"name": name.replace(" ", "") + "_Mesh", "primitives": prims}],
            "skins": [{"name": "Rig", "joints": [J[j] for j in JOINT_NAMES],
                       "inverseBindMatrices": a_ibm, "skeleton": J["Root"]}],
            "materials": materials,
            "animations": animations,
            "accessors": glb.accessors,
            "bufferViews": glb.views,
            "buffers": [{"byteLength": len(glb.blob)}]}

    js = json.dumps(gltf, separators=(",", ":")).encode()
    while len(js) % 4: js += b" "
    binc = bytes(glb.blob)
    while len(binc) % 4: binc += b"\x00"
    total = 12 + 8 + len(js) + 8 + len(binc)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(binc), 0x004E4942)); f.write(binc)
    return geo

# ------------------------------------------------------------------ roster --
#  palette = [primary, secondary, dark, glow]
ROSTER = [
 # -------- CLASSIC GOTHIC --------
 ("Wraith King", "Classic Gothic", dict(
    palette=["3b3a52", "56546e", "23222f", "7df9ff"], scale=1.12, horns="crown",
    weapon="scythe", tail=True, tail_glow=True, eyes=2)),
 ("Bloodmoon Werewolf", "Classic Gothic", dict(
    palette=["6b5346", "4a382e", "2b211a", "ff3b3b"], bulk=1.2, snout=True,
    ears=True, tail=True, claws=True, spikes=True)),
 ("Bone Colossus", "Classic Gothic", dict(
    palette=["d8cfc0", "b6ab97", "6d6355", "ffb347"], scale=1.22, bulk=1.35,
    weapon="club", tusks=True, horns="side", pads=True)),
 ("Spectral Knight", "Classic Gothic", dict(
    palette=["4d5866", "39424d", "20252c", "58c7ff"], pads=True, weapon="sword",
    eyes=1, horns="up", emblem=True)),
 ("Plague Alchemist", "Classic Gothic", dict(
    palette=["44523c", "333d2e", "1e241b", "9dff57"], hood=True, weapon="staff",
    snout=True, eyes=2)),
 # -------- INFERNAL --------
 ("Inferno Golem", "Infernal", dict(
    palette=["3a2f2c", "58423a", "241c19", "ff6a1e"], scale=1.18, bulk=1.4,
    spikes=True, pads=True, claws=True, horns="up", tail=False)),
 ("Lava Imp", "Infernal", dict(
    palette=["7a3020", "5c2416", "331209", "ffce3f"], scale=0.72, horns="up",
    tail=True, tail_glow=True, claws=True, eyes=2)),
 ("Chaos Jester", "Infernal", dict(
    palette=["5b2a6e", "8a3f92", "31173c", "ff5ad9"], horns="side", weapon="sword",
    tail=True, eyes=2)),
 ("Abyss Demon", "Infernal", dict(
    palette=["6e1f2a", "4d151d", "2a0b10", "ff8c42"], scale=1.1, bulk=1.15,
    horns="curved", wings=True, tail=True, weapon="trident", claws=True)),
 ("Void Stalker", "Infernal", dict(
    palette=["1e1b2e", "2c2745", "121020", "b26bff"], eyes=3, claws=True,
    tail=True, tail_glow=True, spikes=True, emblem=False)),
 # -------- FROST & STORM --------
 ("Frost Revenant", "Frost & Storm", dict(
    palette=["9fc4d8", "6f97ad", "3c5666", "aef6ff"], horns="crown",
    weapon="staff", eyes=2, hood=True)),
 ("Storm Djinn", "Frost & Storm", dict(
    palette=["2f4858", "33658a", "1c2b35", "ffe45c"], horns="single",
    wings=True, wing_size=0.8, tail=True, eyes=2)),
 ("Thunder Minotaur", "Frost & Storm", dict(
    palette=["5c4a38", "463628", "281f17", "ffd94a"], scale=1.2, bulk=1.3,
    horns="side", snout=True, weapon="axe", tail=True, pads=True)),
 ("Crystal Basilisk", "Frost & Storm", dict(
    palette=["3f7d63", "2f5d4a", "1b3529", "7dffc8"], snout=True, spikes=True,
    tail=True, tail_glow=True, claws=True, eyes=2, emblem=False)),
 ("Sand Pharaoh", "Frost & Storm", dict(
    palette=["c9a24b", "9c7a35", "584419", "45e0d8"], scale=1.1, horns="crown",
    weapon="staff", pads=True, eyes=2)),
 # -------- ANCIENTS --------
 ("Celestial Guardian", "Ancients", dict(
    palette=["e8e2d0", "c4b895", "77704f", "ffd76a"], scale=1.12, wings=True,
    wing_size=1.15, weapon="sword", pads=True, eyes=1)),
 ("Obsidian Dragonling", "Ancients", dict(
    palette=["262233", "3d3552", "161320", "a05cff"], snout=True, horns="curved",
    wings=True, tail=True, tail_glow=True, claws=True)),
 ("Venom Naga", "Ancients", dict(
    palette=["3e6b3a", "58255e", "1f3a1d", "c8ff3d"], tail=True, tail_glow=True,
    weapon="sword", eyes=2, spikes=True, head_w=1.15)),
 ("Iron Juggernaut", "Ancients", dict(
    palette=["55585e", "3c3f45", "222428", "ff4545"], scale=1.25, bulk=1.5,
    pads=True, weapon="club", eyes=1, spikes=True)),
 ("Shadow Assassin", "Ancients", dict(
    palette=["2b2d33", "3a3d45", "17181c", "51ff9e"], scale=0.95, hood=True,
    weapon="sword", claws=True, tail=False, eyes=2, emblem=False)),
]

def main():
    os.makedirs(os.path.join(OUT, "GLB"), exist_ok=True)
    stats = []
    for name, cat, spec in ROSTER:
        fn = name.replace(" ", "") + ".glb"
        path = os.path.join(OUT, "GLB", fn)
        geo = export_glb(path, name, spec)
        tris = sum(len(v) for v in geo["groups"].values()) // 3
        stats.append((name, cat, fn, tris, os.path.getsize(path)))
        print("  %-24s %-14s %5d tris  %6.1f KB" % (name, cat, tris, os.path.getsize(path)/1024))
    print("Generated %d monsters -> %s" % (len(stats), OUT))
    return stats

if __name__ == "__main__":
    main()
