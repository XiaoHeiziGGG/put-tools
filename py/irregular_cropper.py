from .md import *
from PIL import ImageDraw, ImageFilter
import weakref
import gc
import time

# 使用WeakKeyDictionary自动清理
irregular_crop_node_data = weakref.WeakKeyDictionary()
# 备用清理机制
_node_data_by_id = {}

class IrregularCropper:
    """异形图像裁剪节点 - 支持自由绘制和多边形选择"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "crop_mode": (["free_draw", "polygon"], {"default": "polygon"}),
                "background_fill": (["transparent", "black", "white", "blur"], {"default": "transparent"}),
                "edge_smooth": ("INT", {"default": 0, "min": 0, "max": 20, "step": 1}),
                "auto_crop": ("BOOLEAN", {"default": True}),
                "crop_padding": ("INT", {"default": 10, "min": 0, "max": 100, "step": 1}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("裁剪图像", "选择区域")
    FUNCTION = "irregular_crop"
    CATEGORY = "Put-Tools/Image"

    def irregular_crop(self, image, crop_mode, background_fill, edge_smooth, auto_crop, crop_padding, unique_id):
        node_id = unique_id
        
        try:
            # 清理旧数据
            self._cleanup_old_data()
            
            event = Event()
            
            # 限制图像大小防止内存溢出
            batch_size, height, width, channels = image.shape
            max_size = 4096 * 4096
            if width * height > max_size:
                print(f"[IrregularCropper] 警告: 图像过大 ({width}x{height})，可能导致内存问题")
            
            # 使用较小的图像副本以节省内存
            original_image = image.clone()
            
            # 存储数据
            node_data = {
                "event": event,
                "original_image": original_image,
                "result_image": None,
                "result_mask": None,
                "crop_mode": crop_mode,
                "background_fill": background_fill,
                "edge_smooth": edge_smooth,
                "auto_crop": auto_crop,
                "crop_padding": crop_padding,
                "processing_complete": False,
                "timestamp": time.time()
            }
            
            _node_data_by_id[node_id] = node_data
            
            # 发送预览图像
            try:
                preview_image = (torch.clamp(image.clone(), 0, 1) * 255).cpu().numpy().astype(np.uint8)[0]
                pil_image = Image.fromarray(preview_image)
                
                # 限制预览图像大小
                max_preview_size = (1024, 1024)
                if pil_image.size[0] > max_preview_size[0] or pil_image.size[1] > max_preview_size[1]:
                    pil_image.thumbnail(max_preview_size, Image.LANCZOS)
                
                buffer = io.BytesIO()
                pil_image.save(buffer, format="PNG", optimize=True)
                base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                PromptServer.instance.send_sync("irregular_cropper_update", {
                    "node_id": node_id,
                    "image_data": f"data:image/png;base64,{base64_image}",
                    "crop_mode": crop_mode,
                    "background_fill": background_fill,
                    "edge_smooth": edge_smooth,
                    "auto_crop": auto_crop,
                    "crop_padding": crop_padding
                })
                
                # 等待处理完成
                if not event.wait(timeout=60):
                    print(f"[IrregularCropper] 等待超时: 节点ID {node_id}")
                    self._cleanup_node_data(node_id)
                    return (image, torch.ones((1, image.shape[1], image.shape[2]), dtype=torch.float32))

                # 获取结果
                result_image = image
                result_mask = torch.ones((1, image.shape[1], image.shape[2]), dtype=torch.float32)
                
                if node_id in _node_data_by_id:
                    data = _node_data_by_id[node_id]
                    if data["result_image"] is not None:
                        result_image = data["result_image"]
                    if data["result_mask"] is not None:
                        result_mask = data["result_mask"]
                
                self._cleanup_node_data(node_id)
                return (result_image, result_mask)
                
            except Exception as e:
                print(f"[IrregularCropper] 处理过程中出错: {str(e)}")
                traceback.print_exc()
                self._cleanup_node_data(node_id)
                return (image, torch.ones((1, image.shape[1], image.shape[2]), dtype=torch.float32))
            
        except Exception as e:
            print(f"[IrregularCropper] 节点执行出错: {str(e)}")
            traceback.print_exc()
            self._cleanup_node_data(node_id)
            return (image, torch.ones((1, image.shape[1], image.shape[2]), dtype=torch.float32))
    
    def _cleanup_node_data(self, node_id):
        """清理指定节点的数据"""
        if node_id in _node_data_by_id:
            try:
                data = _node_data_by_id[node_id]
                # 清理大对象
                if "original_image" in data:
                    del data["original_image"]
                if "result_image" in data:
                    del data["result_image"]
                if "result_mask" in data:
                    del data["result_mask"]
                del _node_data_by_id[node_id]
            except Exception as e:
                print(f"[IrregularCropper] 清理数据时出错: {str(e)}")
        
        # 强制垃圾回收
        gc.collect()
    
    def _cleanup_old_data(self):
        """清理过期数据"""
        current_time = time.time()
        expired_keys = []
        
        for node_id, data in _node_data_by_id.items():
            if current_time - data.get("timestamp", 0) > 300:  # 5分钟过期
                expired_keys.append(node_id)
        
        for key in expired_keys:
            self._cleanup_node_data(key)

@PromptServer.instance.routes.post("/irregular_cropper/apply")
async def apply_irregular_cropper(request):
    try:
        data = await request.json()
        node_id = data.get("node_id")
        path_points = data.get("path_points", [])
        image_width = data.get("image_width")
        image_height = data.get("image_height")
        
        # 限制路径点数量
        if len(path_points) > 2000:
            path_points = path_points[:2000]
            print(f"[IrregularCropper] 路径点过多，已限制为2000个点")
        
        if node_id not in _node_data_by_id:
            print(f"[IrregularCropper] 节点数据未找到: {node_id}")
            return web.json_response({"success": False, "error": "节点数据未找到"})
        
        try:
            node_info = _node_data_by_id[node_id]
            original_image = node_info["original_image"]
            
            if path_points and len(path_points) >= 3:
                batch_size, height, width, channels = original_image.shape
                
                # 使用4倍超采样实现抗锯齿
                antialias_scale = 4
                high_res_width = image_width * antialias_scale
                high_res_height = image_height * antialias_scale
                
                # 创建高分辨率mask
                mask_image = Image.new('L', (high_res_width, high_res_height), 0)
                draw = ImageDraw.Draw(mask_image)
                
                # 转换坐标到高分辨率
                polygon_points = []
                for point in path_points:
                    x = int(point['x'] * antialias_scale)
                    y = int(point['y'] * antialias_scale)
                    polygon_points.append((x, y))
                
                # 绘制高分辨率多边形
                if len(polygon_points) >= 3:
                    draw.polygon(polygon_points, fill=255)
                
                # 降采样到原始分辨率实现抗锯齿
                mask_image = mask_image.resize((image_width, image_height), Image.LANCZOS)
                
                # 边缘平滑处理
                if node_info["edge_smooth"] > 0:
                    mask_image = mask_image.filter(ImageFilter.GaussianBlur(radius=node_info["edge_smooth"]/2))
                
                # 调整尺寸以匹配原始图像
                if (image_width, image_height) != (width, height):
                    mask_image = mask_image.resize((width, height), Image.LANCZOS)
                
                # 转换为tensor
                mask_array = np.array(mask_image) / 255.0
                mask_tensor = torch.from_numpy(mask_array).float()
                
                # 处理图像
                processed_images = []
                final_mask = mask_tensor
                
                for b in range(batch_size):
                    img = original_image[b]
                    
                    if node_info["background_fill"] == "transparent":
                        if channels == 3:
                            alpha_channel = mask_tensor.unsqueeze(-1)
                            img_result = torch.cat([img, alpha_channel], dim=-1)
                        else:
                            img_result = img.clone()
                            img_result[:, :, 3] = mask_tensor
                    else:
                        img_result = img.clone()
                        mask_3d = mask_tensor.unsqueeze(-1).expand_as(img)
                        
                        if node_info["background_fill"] == "black":
                            img_result = img * mask_3d
                        elif node_info["background_fill"] == "white":
                            img_result = img * mask_3d + (1 - mask_3d)
                        elif node_info["background_fill"] == "blur":
                            # 简单模糊
                            import torch.nn.functional as F
                            img_blur = img.permute(2, 0, 1).unsqueeze(0)
                            img_blur = F.avg_pool2d(img_blur, kernel_size=9, stride=1, padding=4)
                            img_blur = img_blur.squeeze(0).permute(1, 2, 0)
                            img_result = img * mask_3d + img_blur * (1 - mask_3d)
                    
                    # 自动裁剪
                    if node_info["auto_crop"]:
                        mask_np = mask_tensor.cpu().numpy()
                        rows = np.any(mask_np > 0.1, axis=1)
                        cols = np.any(mask_np > 0.1, axis=0)
                        
                        if rows.any() and cols.any():
                            y_indices = np.where(rows)[0]
                            x_indices = np.where(cols)[0]
                            
                            if len(y_indices) > 0 and len(x_indices) > 0:
                                y_min, y_max = y_indices[0], y_indices[-1]
                                x_min, x_max = x_indices[0], x_indices[-1]
                                
                                padding = node_info["crop_padding"]
                                y_min = max(0, y_min - padding)
                                y_max = min(height, y_max + padding + 1)
                                x_min = max(0, x_min - padding)
                                x_max = min(width, x_max + padding + 1)
                                
                                img_result = img_result[y_min:y_max, x_min:x_max, :]
                                final_mask = mask_tensor[y_min:y_max, x_min:x_max]
                    
                    processed_images.append(img_result)
                
                result_image = torch.stack(processed_images)
                result_mask = final_mask.unsqueeze(0)
                
                node_info["result_image"] = result_image
                node_info["result_mask"] = result_mask
                node_info["event"].set()
                
                print(f"[IrregularCropper] 处理完成，图像形状: {result_image.shape}")
                return web.json_response({"success": True})
            else:
                print(f"[IrregularCropper] 路径点数量不足: {len(path_points)}")
                node_info["event"].set()
                return web.json_response({"success": False, "error": "路径点数量不足"})
            
        except Exception as e:
            print(f"[IrregularCropper] 处理数据时出错: {str(e)}")
            traceback.print_exc()
            if node_id in _node_data_by_id:
                _node_data_by_id[node_id]["event"].set()
            return web.json_response({"success": False, "error": str(e)})

    except Exception as e:
        print(f"[IrregularCropper] 请求处理出错: {str(e)}")
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)})

@PromptServer.instance.routes.post("/irregular_cropper/cancel")
async def cancel_irregular_crop(request):
    try:
        data = await request.json()
        node_id = data.get("node_id")
        
        if node_id in _node_data_by_id:
            _node_data_by_id[node_id]["event"].set()
            print(f"[IrregularCropper] 取消操作: 节点ID {node_id}")
            return web.json_response({"success": True})
        
        return web.json_response({"success": False, "error": "节点未找到"})
        
    except Exception as e:
        print(f"[IrregularCropper] 取消请求出错: {str(e)}")
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)})

NODE_CLASS_MAPPINGS = {
    "IrregularCropper": IrregularCropper,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IrregularCropper": "异形图像裁剪",
}