"""Build the VEYRA studio scene around the 911 model and render jobs.

Usage: python studio.py <model.blend> <jobs.json>
jobs.json: {"scale": 1.0, "samples": 64, "jobs": [{"out": "...png", "cam": "overview",
            "paint": "silver", "wheels": "original", "lid": 0..1, "xray": 0..1}, ...]}
Each job renders an RGBA PNG (transparent studio, shadow catcher floor).
"""
import bpy, bmesh, sys, json, math
from mathutils import Vector, Matrix
import numpy as np

blend, jobs_path = sys.argv[-2], sys.argv[-1]
cfg = json.load(open(jobs_path))
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
O = bpy.data.objects

# ---------------------------------------------------------------- cleanup
for name in ['Cube', 'Sphere', 'Cylinder.002', 'Plane', 'boot.011', 'boot.007', 'Hemi', 'Hemi.001']:
    if name in O: bpy.data.objects.remove(O[name], do_unlink=True)

# ---------------------------------------------------------------- materials
def principled(name, color=(0.8, 0.8, 0.8), metal=0.0, rough=0.5, coat=0.0, alpha=1.0, emission=None, strength=0.0, transmission=0.0, ior=1.45):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Coat Roughness'].default_value = 0.03
    p.inputs['Alpha'].default_value = alpha
    p.inputs['Transmission Weight'].default_value = transmission
    p.inputs['IOR'].default_value = ior
    if emission:
        p.inputs['Emission Color'].default_value = (*emission, 1)
        p.inputs['Emission Strength'].default_value = strength
    nt.links.new(p.outputs[0], out.inputs[0])
    return m, p, out

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

PAINTS = {
    'silver':   dict(color=srgb('#c3c8cc'), metal=0.6, rough=0.36),
    'electric': dict(color=srgb('#d6ee1e'), metal=0.2, rough=0.3),
    'lime':     dict(color=srgb('#7cc21f'), metal=0.3, rough=0.3),
    'sky':      dict(color=srgb('#6f9bc0'), metal=0.5, rough=0.28),
    'graphite': dict(color=srgb('#3a4148'), metal=0.6, rough=0.34),
}

# Body paint with an X-ray mix: 0 = paint, 1 = ghosted shell.
paint, paint_bsdf, paint_out = principled('paint', coat=1.0, **PAINTS['silver'])
def add_xray(mat, bsdf, out, ghost_strength=1.0):
    nt = mat.node_tree
    fres = nt.nodes.new('ShaderNodeLayerWeight'); fres.inputs['Blend'].default_value = 0.35
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.82, 0.92, 1.0, 1)
    em.inputs['Strength'].default_value = 1.6 * ghost_strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    edge = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(fres.outputs['Facing'], edge.inputs[0])
    nt.links.new(tr.outputs[0], edge.inputs[1]); nt.links.new(em.outputs[0], edge.inputs[2])
    mix = nt.nodes.new('ShaderNodeMixShader'); mix.name = 'xray'; mix.inputs[0].default_value = 0
    nt.links.new(bsdf.outputs[0], mix.inputs[1]); nt.links.new(edge.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return mix
xray_mixes = [add_xray(paint, paint_bsdf, paint_out)]

for name, kw, ghost in [
    ('window', dict(color=(0.004, 0.006, 0.008), rough=0.04, coat=0.6), 0.5),
    ('plastic', dict(color=(0.012, 0.013, 0.015), rough=0.55), 0.35),
    ('full_black', dict(color=(0.004, 0.004, 0.004), rough=0.7), 0.25),
    ('silver', dict(color=(0.75, 0.76, 0.78), metal=1.0, rough=0.16), 0.6),
    ('tex_shiny', dict(color=(0.6, 0.6, 0.62), metal=1.0, rough=0.2), 0.6),
    ('lights', dict(color=(0.9, 0.92, 0.95), rough=0.15, emission=(0.9, 0.95, 1.0), strength=1.2), 0.8),
    ('glass', dict(color=(1, 1, 1), rough=0.0, transmission=1.0, ior=1.5), 0.6),
]:
    m, b, o = principled(name, **kw)
    xray_mixes.append(add_xray(m, b, o, ghost))
rubber, *_ = principled('rubber', color=(0.012, 0.012, 0.013), rough=0.8)
caliper, *_ = principled('Material.001', color=srgb('#edff39'), rough=0.35, coat=0.5)

# License plates: blank VEYRA plate.
plate, plate_bsdf, plate_out = principled('license', color=(0.85, 0.86, 0.87), rough=0.35)
xray_mixes.append(add_xray(plate, plate_bsdf, plate_out, 0.4))
if cfg.get('plate'):
    img = bpy.data.images.load(cfg['plate'])
    tex = plate.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img
    plate.node_tree.links.new(tex.outputs['Color'], plate_bsdf.inputs['Base Color'])

# Rims get their own material so wheel finishes do not touch the body trim.
rim, rim_bsdf, _ = principled('rim', color=(0.72, 0.73, 0.75), metal=1.0, rough=0.22)
for n in ['Cylinder.000', 'Cylinder.001']:
    for slot in O[n].material_slots:
        if slot.material and slot.material.name == 'silver': slot.material = rim
RIMS = {
    'original': dict(color=(0.72, 0.73, 0.75), metal=1.0, rough=0.22),
    'aero':     dict(color=(0.72, 0.73, 0.75), metal=1.0, rough=0.22),
    'forged':   dict(color=srgb('#3b3a36'), metal=1.0, rough=0.38),
}

# ---------------------------------------------------------------- front lid
def split_island(obj, test):
    """Move the connected island whose vertices satisfy `test` into a new object."""
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    seen, pick = set(), set()
    for v in bm.verts:
        if v.index in seen: continue
        comp, stack = [], [v]; seen.add(v.index)
        while stack:
            x = stack.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); stack.append(y)
        if test(comp): pick.update(c.index for c in comp)
    bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in obj.data.vertices: v.select = v.index in pick
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    new = [o for o in bpy.context.selected_objects if o != obj][0]
    return new

def is_lid(comp):
    ys = [c.co.y for c in comp]; xs = [c.co.x for c in comp]; zs = [c.co.z for c in comp]
    return min(ys) < -3.3 and max(ys) > -1.3 and max(xs) < 1.2 and min(xs) > -1.2 and min(zs) > -0.2
lid = split_island(O['boot.008'], is_lid); lid.name = 'lid'
lid_mesh_world = [lid.matrix_world @ v.co for v in lid.data.vertices]
hinge_y = max(v.y for v in lid_mesh_world) - 0.05
hinge_z = max(v.z for v in lid_mesh_world if v.y > hinge_y - 0.25)
pivot = bpy.data.objects.new('lid_pivot', None); sc.collection.objects.link(pivot)
pivot.location = (0, hinge_y, hinge_z)
bpy.context.view_layer.update()
lid.parent = pivot; lid.matrix_parent_inverse = pivot.matrix_world.inverted()
LID_OPEN = math.radians(cfg.get('lid_angle', 52))

# Under-lid underside so the open panel is not paper thin from below.
sol = lid.modifiers.new('solid', 'SOLIDIFY'); sol.thickness = 0.02; sol.offset = -1

# ---------------------------------------------------------------- frunk + drive unit
def add(prim, name, mat, **kw):
    getattr(bpy.ops.mesh, prim)(**kw)
    o = bpy.context.active_object; o.name = name
    o.data.materials.clear(); o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    return o

tub_mat, tub_b, tub_o = principled('tub', color=(0.02, 0.025, 0.03), rough=0.75)
xray_mixes.append(add_xray(tub_mat, tub_b, tub_o, 0.3))
motor_mat, *_ = principled('motor', color=srgb('#b9c2c9'), metal=1.0, rough=0.28)
housing_mat, *_ = principled('housing', color=srgb('#5d6a74'), metal=0.9, rough=0.4)
copper, *_ = principled('copper', color=srgb('#c9733c'), metal=1.0, rough=0.3)
hv, *_ = principled('hv', color=srgb('#ff7a1a'), rough=0.4)
acid, *_ = principled('acid', color=srgb('#edff39'), rough=0.3, emission=srgb('#edff39'), strength=0.6)

lid_y0 = min(v.y for v in lid_mesh_world); lid_y1 = max(v.y for v in lid_mesh_world)
cy = (lid_y0 + lid_y1) / 2 + 0.1
tub = add('primitive_cube_add', 'tub', tub_mat, size=1, location=(0, cy, -0.47))
tub.scale = (1.9, (lid_y1 - lid_y0) - 0.45, 0.7)
bm = bmesh.new(); bm.from_mesh(tub.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES'); bm.to_mesh(tub.data); bm.free()
tub.modifiers.new('solid', 'SOLIDIFY').thickness = 0.03
bev = tub.modifiers.new('bevel', 'BEVEL'); bev.width = 0.08; bev.segments = 3
drive = []
stator = add('primitive_cylinder_add', 'stator', housing_mat, radius=0.26, depth=0.62, vertices=64, location=(0.18, cy - 0.05, -0.22), rotation=(0, math.pi / 2, 0))
drive.append(stator)
for i in range(9):
    fin = add('primitive_torus_add', f'fin{i}', motor_mat, major_radius=0.265, minor_radius=0.014, location=(-0.08 + i * 0.065, cy - 0.05, -0.22), rotation=(0, math.pi / 2, 0))
    drive.append(fin)
cap = add('primitive_cylinder_add', 'endcap', motor_mat, radius=0.21, depth=0.06, vertices=64, location=(0.52, cy - 0.05, -0.22), rotation=(0, math.pi / 2, 0)); drive.append(cap)
ring = add('primitive_torus_add', 'accent', acid, major_radius=0.215, minor_radius=0.012, location=(0.555, cy - 0.05, -0.22), rotation=(0, math.pi / 2, 0)); drive.append(ring)
gear = add('primitive_cube_add', 'gearbox', housing_mat, size=1, location=(-0.42, cy - 0.12, -0.26)); gear.scale = (0.34, 0.6, 0.44)
gb = gear.modifiers.new('bevel', 'BEVEL'); gb.width = 0.06; gb.segments = 3; drive.append(gear)
shaft = add('primitive_cylinder_add', 'shaft', motor_mat, radius=0.05, depth=2.2, vertices=32, location=(0, cy - 0.12, -0.42), rotation=(0, math.pi / 2, 0)); drive.append(shaft)
inv = add('primitive_cube_add', 'inverter', housing_mat, size=1, location=(0.05, cy + 0.42, -0.14)); inv.scale = (0.9, 0.3, 0.12)
ib = inv.modifiers.new('bevel', 'BEVEL'); ib.width = 0.03; ib.segments = 3; drive.append(inv)
for i, x in enumerate((-0.18, 0.05, 0.28)):
    curve = bpy.data.curves.new(f'cable{i}', 'CURVE'); curve.dimensions = '3D'; curve.bevel_depth = 0.022; curve.bevel_resolution = 4
    sp = curve.splines.new('BEZIER'); sp.bezier_points.add(1)
    a, b = sp.bezier_points
    a.co = (x, cy + 0.28, -0.12); a.handle_left = (x, cy + 0.35, -0.12); a.handle_right = (x, cy + 0.15, -0.05)
    b.co = (x + 0.05, cy + 0.02, -0.0); b.handle_left = (x + 0.05, cy + 0.1, 0.04); b.handle_right = (x + 0.05, cy - 0.05, -0.04)
    co = bpy.data.objects.new(f'cable{i}', curve); curve.materials.append(hv); sc.collection.objects.link(co); drive.append(co)

# ---------------------------------------------------------------- battery pack (visible in X-ray)
cell_mat, *_ = principled('cells', color=srgb('#2e4f63'), metal=0.6, rough=0.35)
glow, *_ = principled('cellglow', color=srgb('#edff39'), emission=srgb('#edff39'), strength=0.0)
glow_bsdf = glow.node_tree.nodes['Principled BSDF']
pack_parts = []
tray = add('primitive_cube_add', 'tray', housing_mat, size=1, location=(0, 0.1, -0.68)); tray.scale = (2.5, 3.2, 0.1)
tb = tray.modifiers.new('bevel', 'BEVEL'); tb.width = 0.05; tb.segments = 3; pack_parts.append(tray)
for ix in range(4):
    for iy in range(6):
        x = -0.93 + ix * 0.62; y = -1.32 + iy * 0.5 + 0.1
        m = add('primitive_cube_add', f'mod{ix}{iy}', cell_mat, size=1, location=(x, y, -0.57)); m.scale = (0.56, 0.44, 0.13)
        mb = m.modifiers.new('bevel', 'BEVEL'); mb.width = 0.02; mb.segments = 2
        s = add('primitive_cube_add', f'strip{ix}{iy}', glow, size=1, location=(x, y, -0.5)); s.scale = (0.5, 0.05, 0.012)
        pack_parts += [m, s]
for x in (-1.2, 1.2):
    c = add('primitive_cylinder_add', 'hvrail', hv, radius=0.03, depth=3.0, vertices=24, location=(x, 0.1, -0.58), rotation=(math.pi / 2, 0, 0)); pack_parts.append(c)

# ---------------------------------------------------------------- aero discs
def wheel_frames():
    """Return (center, axis, radius) for each visible-side wheel from rim vertices."""
    out = []
    for n in ['Cylinder.000', 'Cylinder.001']:
        o = O[n]; me = o.data; mw = o.matrix_world
        ri = [i for i, s in enumerate(o.material_slots) if s.material == rim][0]
        for side in (1, -1):
            pts = np.array([tuple(mw @ me.vertices[v].co) for p in me.polygons if p.material_index == ri for v in p.vertices])
            pts = pts[pts[:, 0] * side > 0.5] if len(pts) else pts
            if len(pts) < 10: continue
            c = pts.mean(0); u, s_, vt = np.linalg.svd(pts - c); axis = vt[2]
            if axis[0] * side < 0: axis = -axis
            proj = (pts - c) @ axis; outer = proj.max()
            r = np.linalg.norm((pts - c) - np.outer(proj, axis), axis=1).max()
            out.append((Vector(c + axis * (outer - 0.01)), Vector(axis), r))
    return out
discs = []
disc_mat, *_ = principled('disc', color=srgb('#d8dde1'), metal=0.7, rough=0.18, coat=1.0)
for i, (c, axis, r) in enumerate(wheel_frames()):
    d = add('primitive_cylinder_add', f'disc{i}', disc_mat, radius=r * 0.97, depth=0.03, vertices=96, location=c)
    d.rotation_euler = axis.to_track_quat('Z', 'Y').to_euler()
    bv = d.modifiers.new('bevel', 'BEVEL'); bv.width = 0.012; bv.segments = 3
    hub = add('primitive_cylinder_add', f'hub{i}', rim, radius=r * 0.2, depth=0.04, vertices=48, location=c + axis * 0.012)
    hub.rotation_euler = d.rotation_euler
    ringd = add('primitive_torus_add', f'discring{i}', caliper, major_radius=r * 0.72, minor_radius=0.006, location=c + axis * 0.016)
    ringd.rotation_euler = d.rotation_euler
    discs += [d, hub, ringd]

# ---------------------------------------------------------------- studio
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = cfg.get('samples', 64); sc.cycles.use_denoising = True; sc.cycles.seed = 7
sc.cycles.max_bounces = 8; sc.cycles.transparent_max_bounces = 16
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = cfg.get('exposure', -0.35)
sc.render.resolution_x = int(1672 * cfg.get('scale', 1)); sc.render.resolution_y = int(941 * cfg.get('scale', 1))
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'

world = sc.world; wn = world.node_tree.nodes
wn['Background'].inputs[0].default_value = (*srgb('#7896ac'), 1); wn['Background'].inputs[1].default_value = 0.55

floor_z = -1.08
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, floor_z)); floor = bpy.context.active_object; floor.name = 'floor'
floor.is_shadow_catcher = True

def area(name, loc, size, energy, color=(1, 1, 1), shape='RECTANGLE', size_y=None, look=(0, 0, -0.3)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color; l.shape = shape
    l.size = size; l.size_y = size_y or size
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o
area('top', (0, 0, 9), 9, 1500, size_y=12)
area('key', (10, -8, 4), 6, 2600, size_y=2.5)
area('rim_light', (-8, 9, 4), 6, 1300, color=(0.85, 0.92, 1.0))
area('front_fill', (2, -12, 2), 5, 700, color=(0.9, 0.95, 1.0))

# ---------------------------------------------------------------- cameras
def camera(name, target, azimuth, elevation, distance, lens, shift_x=0.0, shift_y=0.0):
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.shift_x = shift_x; cam.shift_y = shift_y
    o = bpy.data.objects.new(name, cam); sc.collection.objects.link(o)
    a, e = math.radians(azimuth), math.radians(elevation)
    pos = Vector(target) + Vector((math.cos(a) * math.cos(e), -math.sin(a) * math.cos(e), math.sin(e))) * distance
    o.location = pos; o.rotation_euler = (Vector(target) - pos).to_track_quat('-Z', 'Y').to_euler()
    return o
CAMS = {k: camera(k, **v) for k, v in cfg['cameras'].items()}

# ---------------------------------------------------------------- jobs
from bpy_extras.object_utils import world_to_camera_view
def project(cam, p):
    v = world_to_camera_view(sc, cam, Vector(p)); return [round(v.x * 100, 2), round((1 - v.y) * 100, 2)]

report = {'points': {}}
for job in cfg['jobs']:
    import os
    if os.path.exists(job['out']) and not cfg.get('force'): print('SKIP', job['out']); continue
    sc.camera = CAMS[job['cam']]
    pk = PAINTS[job.get('paint', 'silver')]
    paint_bsdf.inputs['Base Color'].default_value = (*pk['color'], 1)
    paint_bsdf.inputs['Metallic'].default_value = pk['metal']; paint_bsdf.inputs['Roughness'].default_value = pk['rough']
    rk = RIMS[job.get('wheels', 'original')]
    rim_bsdf.inputs['Base Color'].default_value = (*rk['color'], 1)
    rim_bsdf.inputs['Metallic'].default_value = rk['metal']; rim_bsdf.inputs['Roughness'].default_value = rk['rough']
    for d in discs: d.hide_render = job.get('wheels') != 'aero'
    t = job.get('lid', 0.0)
    pivot.rotation_euler = (-LID_OPEN * t, 0, 0)
    for o in drive + [tub]: o.hide_render = t <= 0.0 and job.get('xray', 0) <= 0
    x = job.get('xray', 0.0)
    for m in xray_mixes: m.inputs[0].default_value = x
    glow_bsdf.inputs['Emission Strength'].default_value = 2.5 * x
    for o in pack_parts: o.hide_render = x <= 0.0
    border = job.get('border')
    sc.render.use_border = bool(border); sc.render.use_crop_to_border = False
    if border: sc.render.border_min_x, sc.render.border_min_y, sc.render.border_max_x, sc.render.border_max_y = border
    sc.render.filepath = job['out']
    bpy.ops.render.render(write_still=True)
    print('RENDERED', job['out'], flush=True)

bpy.context.view_layer.update()
for cam_name, cam in CAMS.items():
    report['points'][cam_name] = {k: project(cam, p) for k, p in cfg.get('points', {}).items()}
json.dump(report, open(cfg.get('report', jobs_path + '.report.json'), 'w'), indent=1)
print('REPORT', json.dumps(report))
