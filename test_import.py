"""
简化测试脚本 - 仅验证基本导入结构
"""
import os
import sys

def test_basic_structure():
    """测试基本文件结构"""
    print("🔍 检查文件结构...")
    
    required_files = [
        "__init__.py",
        "py/__init__.py", 
        "py/md.py",
        "py/irregular_cropper.py",
        "py/mask_white_border.py",
        "web/irregular_cropper.js"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    else:
        print("✅ 所有必需文件存在")
        return True

def test_node_exports():
    """测试节点导出结构"""
    print("\n🔍 检查节点导出...")
    
    # 检查irregular_cropper.py
    try:
        with open("py/irregular_cropper.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "NODE_CLASS_MAPPINGS" in content and "IrregularCropper" in content:
            print("✅ irregular_cropper.py 有正确的导出")
        else:
            print("❌ irregular_cropper.py 缺少导出")
            return False
            
    except Exception as e:
        print(f"❌ 读取irregular_cropper.py失败: {e}")
        return False
    
    # 检查mask_white_border.py  
    try:
        with open("py/mask_white_border.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "NODE_CLASS_MAPPINGS" in content and "MaskWhiteBorder" in content:
            print("✅ mask_white_border.py 有正确的导出")
        else:
            print("❌ mask_white_border.py 缺少导出")
            return False
            
    except Exception as e:
        print(f"❌ 读取mask_white_border.py失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Put-Tools 结构验证测试\n")
    
    # 切换到put-tools目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        test_basic_structure,
        test_node_exports
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 结构验证通过！现在可以测试ComfyUI集成。")
        print("\n📋 下一步：")
        print("1. 确保put-tools在 ComfyUI/custom_nodes/ 目录下")
        print("2. 启动ComfyUI: python main.py") 
        print("3. 查看控制台输出是否显示节点加载成功")
    else:
        print("❌ 存在问题，需要修复。")