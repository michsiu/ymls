import bpy
import sys
import os

argv = sys.argv
argv = argv[argv.index("--") + 1:]

input_file = argv[0]
output_file = argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)

# ⚠️ 关键：检查 operator 是否存在
if hasattr(bpy.ops.wm, "usd_import"):
    bpy.ops.wm.usd_import(filepath=input_file)
else:
    raise Exception("USD Importer not available in this Blender build")

print("FILE EXISTS:", os.path.exists(input_file))
print("FILE SIZE:", os.path.getsize(input_file))

res = bpy.ops.wm.usd_import(filepath=input_file)
print("IMPORT RESULT:", res)

bpy.ops.object.light_add(type='AREA', location=(3, -3, 3))
bpy.ops.object.camera_add(location=(0, -3, 1.5))
bpy.context.scene.camera = bpy.context.object

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'

scene.render.filepath = output_file
bpy.ops.render.render(write_still=True)