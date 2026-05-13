import bpy
import os
import sys
from mathutils import Vector

# =========================
# [[IMPORTANT]] 1. 输入参数
# =========================
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

input_file = argv[0]
output_file = os.path.abspath(argv[1])

print("[[IMPORTANT]] INPUT:", input_file)
print("[[IMPORTANT]] OUTPUT:", output_file)

# =========================
# [[IMPORTANT]] 2. 清空场景
# =========================
bpy.ops.wm.read_factory_settings(use_empty=True)

# =========================
# [[IMPORTANT]] 3. 导入 USDZ
# =========================
bpy.ops.wm.usd_import(filepath=input_file)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']

print("[[IMPORTANT]] MESH COUNT:", len(meshes))

if len(meshes) == 0:
    raise RuntimeError("[[IMPORTANT]] USDZ IMPORT FAILED: no mesh found")

# 打印所有对象（排查白图神器）
print("[[IMPORTANT]] OBJECT LIST:")
for o in bpy.data.objects:
    print(" -", o.name, o.type, o.location)

# =========================
# [[IMPORTANT]] 4. 包围盒 + 居中
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

print("[[IMPORTANT]] MODEL SIZE:", size)
print("[[IMPORTANT]] MODEL CENTER:", center)

for obj in meshes:
    obj.location -= center

# =========================
# [[IMPORTANT]] 5. 统一缩放（保证一致性）
# =========================
target_size = 2.0
scale_factor = target_size / (size if size > 0 else 1)

for obj in meshes:
    obj.scale *= scale_factor

bpy.context.view_layer.update()

print("[[IMPORTANT]] SCALE FACTOR:", scale_factor)

# =========================
# [[IMPORTANT]] 6. 渲染引擎
# =========================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'

scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100

scene.cycles.samples = 64

# =========================
# [[IMPORTANT]] 7. 商品级灯光
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
# [[IMPORTANT]] 8. 白底环境
# =========================
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 1.0

# =========================
# [[IMPORTANT]] 9. 相机（85%填充）
# =========================
fill_ratio = 0.85
cam_dist = size * 2.2 / fill_ratio

bpy.ops.object.camera_add(location=(cam_dist, -cam_dist, cam_dist * 0.8))
cam = bpy.context.object
scene.camera = cam

direction = Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

cam.data.lens = 55

print("[[IMPORTANT]] CAMERA DIST:", cam_dist)

# =========================
# [[IMPORTANT]] 10. 渲染输出
# =========================
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = output_file

print("[[IMPORTANT]] RENDER START")

bpy.ops.render.render(write_still=True)

img = bpy.data.images.get("Render Result")
if img:
    img.save_render(filepath=output_file)

print("[[IMPORTANT]] RENDER DONE")
print("[[IMPORTANT]] FINAL FILE:", output_file)