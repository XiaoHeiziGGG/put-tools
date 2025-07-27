import importlib.util
import os
import sys

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = "web"

def get_ext_dir(subpath=None, mkdir=False):
    dir = os.path.dirname(__file__)
    if subpath is not None:
        dir = os.path.join(dir, subpath)
    
    dir = os.path.abspath(dir)
    
    if mkdir and not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def serialize(obj):
    if isinstance(obj, (str, int, float, bool, list, dict, type(None))):
        return obj
    return str(obj)

# 自动加载py文件夹中的所有节点
py = get_ext_dir("py")
if os.path.exists(py):
    files = os.listdir(py)
    all_nodes = {}
    
    for file in files:
        if not file.endswith(".py") or file.startswith("_") or file == "md.py":
            continue
        
        name = os.path.splitext(file)[0]
        
        try:
            spec = importlib.util.spec_from_file_location(name, os.path.join(py, file))
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"put_tools.{name}"] = module
            spec.loader.exec_module(module)
            
            for item_name in dir(module):
                item = getattr(module, item_name)
                if hasattr(item, "INPUT_TYPES") and callable(getattr(item, "INPUT_TYPES")):
                    all_nodes[item_name] = item
                    
        except Exception as e:
            print(f"加载节点 {name} 时出错: {e}")
            import traceback
            traceback.print_exc()

    # 注册所有找到的节点
    for class_name, class_obj in all_nodes.items():
        NODE_CLASS_MAPPINGS[class_name] = class_obj
        
        # 设置显示名称
        if hasattr(class_obj, 'TITLE'):
            NODE_DISPLAY_NAME_MAPPINGS[class_name] = class_obj.TITLE
        elif hasattr(class_obj, '__doc__') and class_obj.__doc__:
            NODE_DISPLAY_NAME_MAPPINGS[class_name] = class_obj.__doc__.strip().split('\n')[0]
        else:
            NODE_DISPLAY_NAME_MAPPINGS[class_name] = class_name

print(f"Put-Tools: 成功加载 {len(NODE_CLASS_MAPPINGS)} 个节点")
for name in NODE_CLASS_MAPPINGS.keys():
    print(f"  - {name}")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']