import bpy
import sys
import os

print("CWD:", os.getcwd())
print("FILES:", os.listdir("."))

input_file = "model.usdz"

if not os.path.exists(input_file):
    raise SystemExit("❌ 文件不存在")

# 清空场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 只做导入
res = bpy.ops.wm.usd_import(filepath=input_file)
print("IMPORT RESULT:", res)

# 统计对象
print("OBJECT COUNT:", len(bpy.data.objects))

if len(bpy.data.objects) == 0:
    raise SystemExit("❌ 导入失败：空场景")

print("✅ IMPORT OK")