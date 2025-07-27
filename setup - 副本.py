"""
测试脚本 - 验证节点导入是否正常
运行: python test_import.py
"""
import sys
import os

# 添加ComfyUI路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 模拟ComfyUI环境
    import folder_paths
    import nodes
    from server import PromptServer
    
    print("✅ ComfyUI环境模拟成功")
    
    # 测试导入put-tools
    import importlib.util
    spec = importlib.util.spec_from_file_location("put_tools", os.path.join(os.path.dirname(__file__), "__init__.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["put_tools"] = module
    spec.loader.exec_module(module)
    
    print(f"✅ 成功导入Put-Tools")
    print(f"📊 节点数量: {len(module.NODE_CLASS_MAPPINGS)}")
    print(f"📝 节点列表:")
    for name, display_name in module.NODE_DISPLAY_NAME_MAPPINGS.items():
        print(f"  - {name}: {display_name}")
    
    # 测试节点实例化
    for name, node_class in module.NODE_CLASS_MAPPINGS.items():
        try:
            # 测试INPUT_TYPES方法
            input_types = node_class.INPUT_TYPES()
            print(f"✅ {name} INPUT_TYPES 正常")
            
            # 测试节点实例化
            instance = node_class()
            print(f"✅ {name} 实例化成功")
            
        except Exception as e:
            print(f"❌ {name} 测试失败: {e}")
    
    print("\n🎉 所有测试完成！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()