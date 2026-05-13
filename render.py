import bpy
import os
import sys
import math
from mathutils import Vector

# =========================
# [[IMPORTANT]] 输入输出
# =========================
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

input_file = argv[0]
output_file = os.path.abspath(argv[1])

print("[[IMPORTANT]] INPUT:", input_file)
print("[[IMPORTANT]] OUTPUT:", output_file)

# =========================
# 清空场景
# =========================
bpy.ops.wm.read_factory_settings(use_empty=True)

# =========================
# 导入 USDZ
# =========================
bpy.ops.wm.usd_import(filepath=input_file)

objects = list(bpy.data.objects)
meshes = [o for o in objects if o.type == 'MESH']

print("[[IMPORTANT]] OBJECT COUNT:", len(objects))
print("[[IMPORTANT]] MESH COUNT:", len(meshes))

if len(meshes) == 0:
    raise RuntimeError("[[IMPORTANT]] NO MESH FOUND")

# =========================
# 包围盒
# =========================
min_v = Vector((1e10, 1e10, 1e10))
max_v = Vector((-1e10, -1e10, -1e10))

for obj in meshes:
    for v in obj.bound_box:
        w = obj.matrix_world @ Vector(v)
        min_v = Vector((
            min(min_v.x, w.x),
            min(min_v.y, w.y),
            min(min_v.z, w.z)
        ))
        max_v = Vector((
            max(max_v.x, w.x),
            max(max_v.y, w.y),
            max(max_v.z, w.z)
        ))

center = (min_v + max_v) / 2
size = (max_v - min_v).length

print("[[IMPORTANT]] MODEL SIZE:", size)

# =========================
# 居中 + 归一化
# =========================
for obj in meshes:
    obj.location -= center

scale = 2.0 / (size if size > 0 else 1)

for obj in meshes:
    obj.scale *= scale

bpy.context.view_layer.update()

print("[[IMPORTANT]] SCALE:", scale)

# =========================
# 强制可见性（防白图）
# =========================
for o in objects:
    o.hide_set(False)
    o.hide_viewport = False
    if hasattr(o, "hide_render"):
        o.hide_render = False

# =========================
# 灯光（稳定三点光）
# =========================
for o in list(bpy.data.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o)

bpy.ops.object.light_add(type='AREA', location=(4, -4, 5))
key = bpy.context.object
key.data.energy = 1500

bpy.ops.object.light_add(type='AREA', location=(-4, 3, 3))
fill = bpy.context.object
fill.data.energy = 600

bpy.ops.object.light_add(type='AREA', location=(0, 5, 4))
rim = bpy.context.object
rim.data.energy = 400

# =========================
# 🧨 关键修复：删除所有旧相机（白图核心原因）
# =========================
for o in list(bpy.data.objects):
    if o.type == 'CAMERA':
        bpy.data.objects.remove(o)

# =========================
# 📸 单一固定相机（25°稳定构图）
# =========================
cam_dist = 6.0
angle = math.radians(25)

cam_loc = Vector((
    cam_dist * math.cos(angle),
    -cam_dist * math.sin(angle),
    cam_dist * 0.5
))

bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.object
bpy.context.scene.camera = cam

direction = Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

cam.data.lens = 55

print("[[IMPORTANT]] FINAL CAMERA LOCKED")

# =========================
# 渲染设置
# =========================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 256

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024

# =========================
# 白底
# =========================
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.95, 0.95, 0.95, 1)
bg.inputs[1].default_value = 1.0

# =========================
# 输出
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