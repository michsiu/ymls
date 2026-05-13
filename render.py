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

meshes = [o for o in bpy.data.objects if o.type == 'MESH']

print("[[IMPORTANT]] MESH COUNT:", len(meshes))

if len(meshes) == 0:
    raise RuntimeError("[[IMPORTANT]] IMPORT FAILED: no mesh")

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
# 居中
# =========================
for obj in meshes:
    obj.location -= center

# =========================
# 🔥 工业级关键：统一归一化（核心）
# =========================
target_size = 2.0
scale = target_size / (size if size > 0 else 1)

for obj in meshes:
    obj.scale *= scale

bpy.context.view_layer.update()

print("[[IMPORTANT]] NORMALIZED SCALE:", scale)

# =========================
# 渲染引擎（稳定优先）
# =========================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64

scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100

# =========================
# 白底环境
# =========================
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 1.0

# =========================
# 🔥 工业级固定相机（重点）
# =========================
bpy.ops.object.camera_add(location=(5, -5, 3))
cam = bpy.context.object
scene.camera = cam

direction = Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

cam.data.lens = 55

print("[[IMPORTANT]] CAMERA FIXED POSITION")

# =========================
# 灯光（标准三点光）
# =========================
bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
key = bpy.context.object
key.data.energy = 900

bpy.ops.object.light_add(type='AREA', location=(-3, 2, 3))
fill = bpy.context.object
fill.data.energy = 300

bpy.ops.object.light_add(type='AREA', location=(0, 3, 4))
rim = bpy.context.object
rim.data.energy = 250

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
print("[[IMPORTANT]] FINAL:", output_file)