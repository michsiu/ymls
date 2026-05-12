import bpy
import os
import math
from mathutils import Vector

# =========================
# 1. 输入 / 输出
# =========================
input_file = "model.usdz"
output_file = os.path.abspath("output.png")

print("CWD:", os.getcwd())
print("INPUT EXISTS:", os.path.exists(input_file))
print("OUTPUT:", output_file)

if not os.path.exists(input_file):
    raise SystemExit("❌ model.usdz 不存在")

# =========================
# 2. 清空场景
# =========================
bpy.ops.wm.read_factory_settings(use_empty=True)

# =========================
# 3. 导入 USDZ
# =========================
res = bpy.ops.wm.usd_import(filepath=input_file)
print("IMPORT RESULT:", res)

# =========================
# 4. 获取 mesh
# =========================
meshes = [o for o in bpy.data.objects if o.type == 'MESH']

if not meshes:
    raise RuntimeError("❌ 没有可渲染 mesh（import失败或空场景）")

# =========================
# 5. 计算 bounding box（核心：防黑图）
# =========================
min_v = Vector((1e10, 1e10, 1e10))
max_v = Vector((-1e10, -1e10, -1e10))

for obj in meshes:
    for v in obj.bound_box:
        world_v = obj.matrix_world @ Vector(v)
        min_v = Vector((
            min(min_v.x, world_v.x),
            min(min_v.y, world_v.y),
            min(min_v.z, world_v.z),
        ))
        max_v = Vector((
            max(max_v.x, world_v.x),
            max(max_v.y, world_v.y),
            max(max_v.z, world_v.z),
        ))

center = (min_v + max_v) / 2
size = (max_v - min_v).length

print("CENTER:", center)
print("SIZE:", size)

# =========================
# 6. 移动模型到原点
# =========================
for obj in meshes:
    obj.location -= center

# =========================
# 7. 相机（自动适配）
# =========================
cam_dist = max(size * 2.5, 2.0)

bpy.ops.object.camera_add(location=(0, -cam_dist, cam_dist * 0.5))
cam = bpy.context.object
bpy.context.scene.camera = cam

cam.data.clip_start = 0.01
cam.data.clip_end = 10000

# 看向原点
direction = Vector((0, 0, 0)) - cam.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()

# =========================
# 8. 光照（防黑图关键）
# =========================
bpy.ops.object.light_add(type='SUN', location=(5, -5, 5))
light = bpy.context.object
light.data.energy = 5

# =========================
# 9. world light（双保险）
# =========================
world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 2.0

# =========================
# 10. 渲染设置
# =========================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16

scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = output_file

# =========================
# 11. 渲染 + 强制落盘
# =========================
print("START RENDER")

bpy.ops.render.render(write_still=True)

img = bpy.data.images.get("Render Result")
if img:
    img.save_render(filepath=output_file)
    print("SAVED:", output_file)

print("DONE")