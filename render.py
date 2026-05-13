import bpy
import os
from mathutils import Vector

# =========================
# 固定输入输出（由 YAML 传入）
# =========================
import sys

MODEL = sys.argv[-2]
OUTPUT = sys.argv[-1]

print("INPUT:", MODEL)
print("OUTPUT:", OUTPUT)

bpy.ops.wm.read_factory_settings(use_empty=True)

# =========================
# USDZ import
# =========================
bpy.ops.wm.usd_import(filepath=MODEL)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
if not meshes:
    raise RuntimeError("no mesh found")

# =========================
# bounding box
# =========================
min_v = Vector((1e10,1e10,1e10))
max_v = Vector((-1e10,-1e10,-1e10))

for obj in meshes:
    for v in obj.bound_box:
        w = obj.matrix_world @ Vector(v)
        min_v = Vector((
            min(min_v.x,w.x),
            min(min_v.y,w.y),
            min(min_v.z,w.z)
        ))
        max_v = Vector((
            max(max_v.x,w.x),
            max(max_v.y,w.y),
            max(max_v.z,w.z)
        ))

center = (min_v + max_v) / 2
size = (max_v - min_v).length

for obj in meshes:
    obj.location -= center

# =========================
# camera（45°商品视角）
# =========================
cam_dist = size * 2.2

bpy.ops.object.camera_add(location=(cam_dist, -cam_dist, cam_dist * 0.6))
cam = bpy.context.object
bpy.context.scene.camera = cam

direction = Vector((0,0,0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()

cam.data.lens = 50

# =========================
# light
# =========================
bpy.ops.object.light_add(type='SUN', location=(5,-5,5))
light = bpy.context.object
light.data.energy = 4

# =========================
# white background
# =========================
world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1,1,1,1)
bg.inputs[1].default_value = 1.2

# =========================
# render（正方形）
# =========================
scene = bpy.context.scene
scene.render.engine = 'Cycles'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024

scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = OUTPUT

bpy.ops.render.render(write_still=True)

img = bpy.data.images.get("Render Result")
if img:
    img.save_render(filepath=OUTPUT)

print("DONE:", OUTPUT)