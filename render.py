import bpy
import os
import sys
import math
from mathutils import Vector

# =========================
# [[IMPORTANT]] IO
# =========================
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

input_file = argv[0]
output_file = os.path.abspath(argv[1])

print("[[IMPORTANT]] INPUT:", input_file)
print("[[IMPORTANT]] OUTPUT:", output_file)

# =========================
# clean scene
# =========================
bpy.ops.wm.read_factory_settings(use_empty=True)

# =========================
# import USDZ
# =========================
bpy.ops.wm.usd_import(filepath=input_file)

objects = list(bpy.data.objects)
meshes = [o for o in objects if o.type == 'MESH']

print("[[IMPORTANT]] OBJECT COUNT:", len(objects))
print("[[IMPORTANT]] MESH COUNT:", len(meshes))

if not meshes:
    raise RuntimeError("NO MESH FOUND")

# =========================
# bbox compute
# =========================
min_v = Vector((1e10,1e10,1e10))
max_v = Vector((-1e10,-1e10,-1e10))

for obj in meshes:
    for v in obj.bound_box:
        w = obj.matrix_world @ Vector(v)
        min_v = Vector((min(min_v.x,w.x), min(min_v.y,w.y), min(min_v.z,w.z)))
        max_v = Vector((max(max_v.x,w.x), max(max_v.y,w.y), max(max_v.z,w.z)))

center = (min_v + max_v) / 2
size = (max_v - min_v).length

print("[[IMPORTANT]] MODEL SIZE:", size)

for obj in meshes:
    obj.location -= center

scale = 2.0 / (size if size > 0 else 1)
for obj in meshes:
    obj.scale *= scale

bpy.context.view_layer.update()

# =========================
# lights (stable studio)
# =========================
for o in list(bpy.data.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o)

def add_light(loc, energy):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object
    l.data.energy = energy
    return l

add_light((4,-4,5),1500)
add_light((-4,3,3),600)
add_light((0,5,4),400)

# =========================
# CAMERA VALIDATION CORE
# =========================

def create_camera(angle_deg):
    rad = math.radians(angle_deg)

    cam_loc = Vector((
        6 * math.cos(rad),
        -6 * math.sin(rad),
        3
    ))

    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object

    direction = Vector((0,0,0)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()

    bpy.context.scene.camera = cam
    return cam

def check_visibility(cam):
    scene = bpy.context.scene
    bpy.context.view_layer.update()

    # 简单投影检测：bbox中心是否在camera前方
    cam_loc = cam.location

    for m in meshes:
        world_pos = m.matrix_world.translation
        vec = world_pos - cam_loc

        # dot product approx forward check
        forward = Vector((0,0,0)) - cam_loc
        if vec.dot(forward) < 0:
            return False

    return True

# =========================
# AUTO CAMERA SEARCH (WHITE-FREE SYSTEM)
# =========================
angles = [15, 25, 35, 45, 60]

cam = None

for a in angles:
    cam = create_camera(a)

    ok = check_visibility(cam)

    print("[[IMPORTANT]] ANGLE", a, "VISIBLE:", ok)

    if ok:
        print("[[IMPORTANT]] SELECTED ANGLE:", a)
        break

# fallback
if cam is None:
    cam = create_camera(25)

# =========================
# render settings
# =========================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 256

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024

# white bg
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.95,0.95,0.95,1)
bg.inputs[1].default_value = 1.0

# =========================
# render
# =========================
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = output_file

print("[[IMPORTANT]] RENDER START")

bpy.ops.render.render(write_still=True)

img = bpy.data.images.get("Render Result")
if img:
    img.save_render(filepath=output_file)

print("[[IMPORTANT]] RENDER DONE")
print("[[IMPORTANT]] OUTPUT READY:", output_file)