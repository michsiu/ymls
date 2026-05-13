import bpy
import os
import sys
from mathutils import Vector
import math

# =========================
# 1. 参数输入
# =========================
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

input_file = argv[0]
output_file = os.path.abspath(argv[1])

print("INPUT:", input_file)
print("OUTPUT:", output_file)

# =========================
# 2. 清空场景
# =========================
bpy.ops.wm.read_factory_settings(use_empty=True)

# =========================
# 3. 导入 USDZ
# =========================
bpy.ops.wm.usd_import(filepath=input_file)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
if not meshes:
    raise RuntimeError("❌ No mesh found")

# =========================
# 4. 计算包围盒 + 居中 + 缩放统一
# =========================
min_v = Vector((1e10, 1e10, 1e10))
max_v = Vector((-1e10, -1e10, -1e10))

for obj in meshes:
    for v in obj.bound_box:
        wv = obj.matrix_world @ Vector(v)
        min_v = Vector((
            min(min_v.x, wv.x),
            min(min_v.y, wv.y),
            min(min_v.z, wv.z)
        ))
        max_v = Vector((
            max(max_v.x, wv.x),
            max(max_v.y, wv.y),
            max(max_v.z, wv.z)
        ))

center = (min_v + max_v) / 2
size = (max_v - min_v).length

for obj in meshes:
    obj.location -= center

# =========================
# 5. 固定缩放（统一视觉尺度）
# =========================
target_size = 2.0
scale_factor = target_size / (size if size > 0 else 1)

for obj in meshes:
    obj.scale *= scale_factor

bpy.context.view_layer.update()

# =========================
# 6. Eevee 渲染（稳定快速）
# =========================
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'

scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100

scene.eevee.use_gtao = True
scene.eevee.use_ssr = False   # 稳定优先（避免 CI 崩）
scene.eevee.use_bloom = False  # 避免发光污染

# =========================
# 7. 商品级三点布光
# =========================
bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
key = bpy.context.object
key.data.energy = 900
key.data.size = 4

bpy.ops.object.light_add(type='AREA', location=(-3, 2, 3))
fill = bpy.context.object
fill.data.energy = 300
fill.data.size = 5

bpy.ops.object.light_add(type='AREA', location=(0, 3, 4))
rim = bpy.context.object
rim.data.energy = 250
rim.data.size = 3

# =========================
# 8. 白底环境
# =========================
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 1.0

# =========================
# 9. 相机（关键：85%占比构图）
# =========================
fill_ratio = 0.85

cam_dist = size * 2.2
cam_dist = cam_dist / fill_ratio  # 控制填充比例

bpy.ops.object.camera_add(location=(cam_dist, -cam_dist, cam_dist * 0.8))
cam = bpy.context.object
scene.camera = cam

direction = Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

cam.data.lens = 55
cam.data.clip_start = 0.01
cam.data.clip_end = 10000

# =========================
# 10. 渲染输出
# =========================
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = output_file

print("RENDER START")

bpy.ops.render.render(write_still=True)

img = bpy.data.images.get("Render Result")
if img:
    img.save_render(filepath=output_file)

print("DONE:", output_file)