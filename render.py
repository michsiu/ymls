import bpy
import os
import math
from mathutils import Vector

# =========================
# 1. 输入文件 & 输出文件
# =========================
input_file = "model.usdz"

base_name = os.path.splitext(os.path.basename(input_file))[0]
output_file = os.path.abspath(f"{base_name}.png")

print("INPUT:", input_file)
print("OUTPUT:", output_file)

if not os.path.exists(input_file):
    raise SystemExit("❌ USDZ 不存在")

# =========================
# 2. 清空场景
# =========================
bpy.ops.wm.read_factory_settings(use_empty=True)

# =========================
# 3. 导入 USDZ
# =========================
res = bpy.ops.wm.usd_import(filepath=input_file)
print("IMPORT:", res)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']

if not meshes:
    raise RuntimeError("❌ 没有 mesh")

# =========================
# 4. 计算 bounding box（自动居中）
# =========================
min_v = Vector((1e10, 1e10, 1e10))
max_v = Vector((-1e10, -1e10, -1e10))

for obj in meshes:
    for v in obj.bound_box:
        wv = obj.matrix_world @ Vector(v)
        min_v = Vector((min(min_v.x, wv.x), min(min_v.y, wv.y), min(min_v.z, wv.z)))
        max_v = Vector((max(max_v.x, wv.x), max(max_v.y, wv.y), max(max_v.z, wv.z)))

center = (min_v + max_v) / 2
size = (max_v - min_v).length

for obj in meshes:
    obj.location -= center

print("CENTERED OK")

# =========================
# 5. 相机（45° 侧视 + 商品角度）
# =========================
cam_dist = size * 2.2

bpy.ops.object.camera_add(location=(cam_dist * 0.8, -cam_dist, cam_dist * 0.6))
cam = bpy.context.object
bpy.context.scene.camera = cam

cam.data.lens = 50  # 商品常用焦距
cam.data.clip_start = 0.01
cam.data.clip_end = 10000

# look at origin
direction = Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# =========================
# 6. 光照（柔和商品光）
# =========================
bpy.ops.object.light_add(type='AREA', location=(2, -2, 3))
key_light = bpy.context.object
key_light.data.energy = 300
key_light.data.size = 3

bpy.ops.object.light_add(type='AREA', location=(-2, -1, 2))
fill_light = bpy.context.object
fill_light.data.energy = 120
fill_light.data.size = 5

# =========================
# 7. 白底环境（电商风格）
# =========================
world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 1.2

# =========================
# 8. 渲染设置（高质量CPU）
# =========================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100

scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = output_file

# =========================
# 9. 渲染 + 强制保存
# =========================
print("RENDER START")

bpy.ops.render.render(write_still=True)

img = bpy.data.images.get("Render Result")
if img:
    img.save_render(filepath=output_file)

print("DONE:", output_file)