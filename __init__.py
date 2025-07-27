import importlib
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

# 采用成功节点的加载方式
py = get_ext_dir("py")
if os.path.exists(py):
    files = os.listdir(py)
    all_nodes = {}
    
    for file in files:
        if not file.endswith(".py") or file.startswith("_") or file == "md.py":
            continue
        
        name = os.path.splitext(file)[0]
        
        try:
            # 使用正确的包导入方式
            imported_module = importlib.import_module(".py.{}".format(name), __name__)
            
            # 合并节点映射
            if hasattr(imported_module, 'NODE_CLASS_MAPPINGS'):
                NODE_CLASS_MAPPINGS = {**NODE_CLASS_MAPPINGS, **imported_module.NODE_CLASS_MAPPINGS}
            
            if hasattr(imported_module, 'NODE_DISPLAY_NAME_MAPPINGS'):
                NODE_DISPLAY_NAME_MAPPINGS = {**NODE_DISPLAY_NAME_MAPPINGS, **imported_module.NODE_DISPLAY_NAME_MAPPINGS}
            
            # 序列化映射
            if hasattr(imported_module, 'NODE_CLASS_MAPPINGS'):
                serialized_CLASS_MAPPINGS = {k: serialize(v) for k, v in imported_module.NODE_CLASS_MAPPINGS.items()}
                serialized_DISPLAY_NAME_MAPPINGS = {k: serialize(v) for k, v in imported_module.NODE_DISPLAY_NAME_MAPPINGS.items()}
                all_nodes[file] = {
                    "NODE_CLASS_MAPPINGS": serialized_CLASS_MAPPINGS, 
                    "NODE_DISPLAY_NAME_MAPPINGS": serialized_DISPLAY_NAME_MAPPINGS
                }
                
        except Exception as e:
            print(f"加载节点 {name} 时出错: {e}")
            import traceback
            traceback.print_exc()

print(f"Put-Tools: 成功加载 {len(NODE_CLASS_MAPPINGS)} 个节点")
for name in NODE_CLASS_MAPPINGS.keys():
    print(f"  - {name}")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']