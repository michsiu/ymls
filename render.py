import bpy
import os
import sys
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

# =========================
# 🚨 强制兜底：没有 mesh 直接报错
# =========================
if len(meshes) == 0:
    raise RuntimeError("[[IMPORTANT]] NO MESH FOUND - USDZ IMPORT FAILED")

# =========================
# 包围盒计算
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
# 居中模型
# =========================
for obj in meshes:
    obj.location -= center

bpy.context.view_layer.update()

# =========================
# 🚨 强制归一化（防飞出画面）
# =========================
target = 2.0
scale = target / (size if size > 0 else 1)

for obj in meshes:
    obj.scale *= scale

bpy.context.view_layer.update()

print("[[IMPORTANT]] SCALE:", scale)

# =========================
# 🔥 强制可见性修复（防白图关键）
# =========================
for obj in objects:
    obj.hide_set(False)
    obj.hide_viewport = False
    if hasattr(obj, "hide_render"):
        obj.hide_render = False

# =========================
# 渲染引擎（稳定优先）
# =========================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64

scene.render.resolution_x = 512
scene.render.resolution_y = 512

# =========================
# 世界（避免纯白吞模型）
# =========================
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.9, 0.9, 0.9, 1)
bg.inputs[1].default_value = 1.0

# =========================
# 灯光（强制可见）
# =========================
bpy.ops.object.light_add(type='AREA', location=(5, -5, 5))
key = bpy.context.object
key.data.energy = 1200

bpy.ops.object.light_add(type='AREA', location=(-5, 3, 4))
fill = bpy.context.object
fill.data.energy = 400

bpy.ops.object.light_add(type='AREA', location=(0, 5, 5))
rim = bpy.context.object
rim.data.energy = 300

# =========================
# 🚨 强制相机（防白图核心）
# =========================
bpy.ops.object.camera_add(location=(6, -6, 4))
cam = bpy.context.object
scene.camera = cam

direction = Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

cam.data.lens = 55

# =========================
# 🚨 强制“看向物体”（最终防白图）
# =========================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.view3d.camera_to_view_selected()

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