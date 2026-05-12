import bpy
import os
import sys

# =========================
# 1. 固定路径（CI根目录）
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
# 4. 强制保证有内容（防空场景）
# =========================
if len(bpy.data.objects) == 0:
    print("⚠️ 空场景，创建占位立方体")
    bpy.ops.mesh.primitive_cube_add()

# =========================
# 5. 强制光照（避免黑图）
# =========================
world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 2.0

bpy.ops.object.light_add(type='AREA', location=(3, -3, 3))

# =========================
# 6. 相机（确保一定能看到）
# =========================
bpy.ops.object.camera_add(location=(0, -3, 1.5))
bpy.context.scene.camera = bpy.context.object

# =========================
# 7. 渲染设置（稳定模式）
# =========================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16

scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = output_file

# =========================
# 8. 渲染 + 强制落盘（关键）
# =========================
print("START RENDER")

bpy.ops.render.render(write_still=True)

# 🔥 强制写文件（防 CI bug）
img = bpy.data.images.get("Render Result")
if img:
    img.save_render(filepath=output_file)
    print("SAVED via image API")

print("DONE:", output_file)