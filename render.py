import bpy
import os

input_file = "model.usdz"   # 根目录固定文件
output_file = "output.png"

print("CWD:", os.getcwd())
print("CHECK FILE:", os.path.exists(input_file))

if not os.path.exists(input_file):
    raise FileNotFoundError("model.usdz 不存在（根目录）")

# 清空场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 导入 USDZ
if hasattr(bpy.ops.wm, "usd_import"):
    bpy.ops.wm.usd_import(filepath=input_file)
else:
    raise RuntimeError("USD importer 不可用")

# 光照（避免黑图）
world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 2.0

bpy.ops.object.light_add(type='AREA', location=(3, -3, 3))

# 相机
bpy.ops.object.camera_add(location=(0, -3, 1.5))
bpy.context.scene.camera = bpy.context.object

# 渲染
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.render.filepath = output_file

bpy.ops.render.render(write_still=True)

print("DONE:", output_file)