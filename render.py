import bpy
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:]

input_file = argv[0]
output_file = argv[1]

# 清空场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 导入 USDZ
bpy.ops.wm.usd_import(filepath=input_file)

# 加灯光（否则黑图）
bpy.ops.object.light_add(type='AREA', location=(3, -3, 3))

# 加相机
bpy.ops.object.camera_add(location=(0, -3, 1.5))
bpy.context.scene.camera = bpy.context.object

# 渲染设置（避免 GPU）
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'   # ⚠️关键：避免 iGL / GPU

scene.render.filepath = output_file

# 渲染
bpy.ops.render.render(write_still=True)