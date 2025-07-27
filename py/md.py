"""
Put-Tools 核心依赖和工具函数
提供ComfyUI节点开发所需的基础功能
"""

import time
import torch
import numpy as np
import cv2
import os
import sys
import folder_paths
import base64
import io
import traceback

try:
    import torchvision.transforms.v2 as T
except ImportError:
    import torchvision.transforms as T

from aiohttp import web
from PIL import Image, ImageOps
from io import BytesIO
from threading import Event
from nodes import LoadImage, PreviewImage
from server import PromptServer

routes = PromptServer.instance.routes

class AlwaysEqualProxy(str):
    """总是返回相等的代理类，用于特殊类型匹配"""
    def __eq__(self, _):
        return True

    def __ne__(self, _):
        return False
    
class AnyType(str):
    """用于表示任意类型的特殊类，在类型比较时总是返回相等"""
    def __eq__(self, _) -> bool:
        return True

    def __ne__(self, __value: object) -> bool:
        return False

# 全局任意类型实例
any = AnyType("*")

# 版本信息
__version__ = "1.0.0"
__author__ = "Put-Tools Contributors"
__email__ = ""
__description__ = "ComfyUI异形图像处理工具集"