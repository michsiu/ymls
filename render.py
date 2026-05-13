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

# 居中
for obj in meshes:
    obj.location -= center

bpy.context.view_layer.update()

# =========================
# 归一化缩放（保证统一视觉）
# =========================
target_size = 2.0
scale = target_size / (size if size > 0 else 1)

for obj in meshes:
    obj.scale *= scale

bpy.context.view_layer.update()

print("[[IMPORTANT]] SCALE:", scale)

# =========================
# 材质轻修复（USDZ常见问题）
# =========================
for mat in bpy.data.materials:
    if mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                n.image.reload()

            if n.type == "BSDF_PRINCIPLED":
                try:
                    n.inputs["Roughness"].default_value *= 0.85
                    n.inputs["Specular"].default_value = 0.5
                except:
                    pass

# =========================
# 摄影棚灯光（三点光）
# =========================
for o in list(bpy.data.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o)

bpy.ops.object.light_add(type='AREA', location=(4, -4, 5))
key = bpy.context.object
key.data.energy = 1500
key.data.size = 3

bpy.ops.object.light_add(type='AREA', location=(-4, 3, 3))
fill = bpy.context.object
fill.data.energy = 600
fill.data.size = 5

bpy.ops.object.light_add(type='AREA', location=(0, 5, 4))
rim = bpy.context.object
rim.data.energy = 400
rim.data.size = 4

# =========================
# 自动最佳角度（占比评分）
# =========================
def bbox_area(objs):
    coords = []
    for o in objs:
        coords += [o.matrix_world @ Vector(v) for v in o.bound_box]

    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    return (max(xs)-min(xs)) * (max(ys)-min(ys))

def try_angle(angle_deg):
    rad = math.radians(angle_deg)

    cam_loc = Vector((
        6 * math.cos(rad),
        -6 * math.sin(rad),
        3
    ))

    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object

    direction = Vector((0, 0, 0)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    bpy.context.scene.camera = cam
    bpy.context.view_layer.update()

    return bbox_area(meshes)

angles = [15, 25, 35, 45, 60]

best_angle = 25
best_score = -1

for a in angles:
    score = try_angle(a)
    print("[[IMPORTANT]] ANGLE", a, "SCORE", score)

    if score > best_score:
        best_score = score
        best_angle = a

print("[[IMPORTANT]] BEST ANGLE:", best_angle)

# =========================
# 固定最佳相机重新创建
# =========================
rad = math.radians(best_angle)

cam_loc = Vector((
    6 * math.cos(rad),
    -6 * math.sin(rad),
    3
))

bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.object
bpy.context.scene.camera = cam

direction = Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

cam.data.lens = 55

# =========================
# 渲染设置
# =========================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 256

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024

# 白底
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