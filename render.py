import bpy
import os
import sys
from mathutils import Vector

# =========================
# 1. 读取参数
# =========================
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else argv

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
    raise RuntimeError("❌ no mesh found")

# =========================
# 4. 计算包围盒 + 居中
# =========================
min_v = Vector((1e10,1e10,1e10))
max_v = Vector((-1e10,-1e10,-1e10))

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

for obj in meshes:
    obj.location -= center

# =========================
# 5. Eevee（关键：更像产品图）
# =========================
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'

scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100

scene.eevee.use_gtao = True          # 环境光遮蔽
scene.eevee.use_bloom = True         # 轻微发光
scene.eevee.use_ssr = True           # 屏幕空间反射

# =========================
# 6. 相机（商品45°）
# =========================
cam_dist = size * 2.2

bpy.ops.object.camera_add(location=(cam_dist, -cam_dist, cam_dist * 0.8))
cam = bpy.context.object
scene.camera = cam

direction = Vector((0,0,0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()

cam.data.lens = 55
cam.data.clip_start = 0.01
cam.data.clip_end = 10000

# =========================
# 7. 三点布光（商品摄影标准）
# =========================

# 主光
bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
key = bpy.context.object
key.data.energy = 800
key.data.size = 4

# 辅光
bpy.ops.object.light_add(type='AREA', location=(-3, 2, 3))
fill = bpy.context.object
fill.data.energy = 250
fill.data.size = 5

# 背光（轮廓）
bpy.ops.object.light_add(type='AREA', location=(0, 3, 4))
rim = bpy.context.object
rim.data.energy = 300
rim.data.size = 3

# =========================
# 8. 白底世界（干净电商风）
# =========================
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 1.0

# =========================
# 9. 渲染设置（Eevee 快速输出）
# =========================
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = output_file

# =========================
# 10. 渲染
# =========================
print("RENDER START")

bpy.ops.render.render(write_still=True)

img = bpy.data.images.get("Render Result")
if img:
    img.save_render(filepath=output_file)

print("DONE:", output_file)