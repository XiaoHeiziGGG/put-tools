from .md import *
from PIL import ImageDraw, ImageFilter
import cv2

class MaskWhiteBorder:
    """根据mask自动剪裁异形区域并添加白边"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "border_width": ("INT", {"default": 20, "min": 0, "max": 200, "step": 1}),
                "border_color": (["white", "black", "gray"], {"default": "white"}),
                "auto_crop": ("BOOLEAN", {"default": True}),
                "crop_padding": ("INT", {"default": 10, "min": 0, "max": 100, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("cropped_with_border",)
    FUNCTION = "crop_with_border"
    CATEGORY = "Put-Tools/Image"

    def crop_with_border(self, image, mask, border_width, border_color, auto_crop, crop_padding):
        batch_size, height, width, channels = image.shape
        
        results = []
        
        for i in range(batch_size):
            img_tensor = image[i]
            mask_tensor = mask[i] if i < len(mask) else mask[0]
            
            # 转换为PIL
            img_np = (img_tensor * 255).cpu().numpy().astype(np.uint8)
            mask_np = (mask_tensor * 255).cpu().numpy().astype(np.uint8)
            
            img_pil = Image.fromarray(img_np)
            mask_pil = Image.fromarray(mask_np, mode='L')
            
            # 1. 创建带alpha通道的图像（物体区域保留，其他透明）
            img_with_alpha = img_pil.convert('RGBA')
            img_with_alpha.putalpha(mask_pil)  # 物体区域不透明，其他透明
            
            # 2. 创建边框区域
            if border_width > 0:
                # 扩展mask创建边框区域
                border_mask = self.create_border_mask(mask_pil, border_width)
                
                # 创建边框图像
                border_img = self.create_border_image(width, height, border_color)
                
                # 合成：先放边框，再放物体
                final_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                
                # 添加边框（只在边框区域）
                final_img = Image.composite(border_img, final_img, border_mask)
                
                # 添加原始物体（覆盖在边框上）
                final_img = Image.alpha_composite(final_img, img_with_alpha)
            else:
                final_img = img_with_alpha
            
            # 3. 自动裁剪到最小边界框
            if auto_crop:
                # 创建完整的mask（物体+边框）
                full_mask = border_mask if border_width > 0 else mask_pil
                if border_width > 0:
                    # 合并物体mask和边框mask
                    full_mask = Image.composite(mask_pil, border_mask, mask_pil)
                
                # 获取边界框
                bbox = full_mask.getbbox()
                if bbox:
                    # 添加padding
                    left, top, right, bottom = bbox
                    left = max(0, left - crop_padding)
                    top = max(0, top - crop_padding)
                    right = min(width, right + crop_padding)
                    bottom = min(height, bottom + crop_padding)
                    
                    # 裁剪图像
                    final_img = final_img.crop((left, top, right, bottom))
            
            # 转换回tensor
            final_np = np.array(final_img).astype(np.float32) / 255.0
            final_tensor = torch.from_numpy(final_np).unsqueeze(0)
            
            results.append(final_tensor)
        
        result = torch.cat(results, dim=0)
        return (result,)
    
    def create_border_mask(self, mask_pil, border_width):
        """创建边框mask"""
        mask_np = np.array(mask_pil)
        
        # 创建膨胀核
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (border_width*2+1, border_width*2+1))
        
        # 膨胀操作创建外扩区域
        dilated = cv2.dilate(mask_np, kernel, iterations=1)
        
        # 边框区域 = 膨胀区域 - 原始区域（只要边框部分）
        border_area = cv2.subtract(dilated, mask_np)
        
        border_mask = Image.fromarray(border_area, mode='L')
        return border_mask
    
    def create_border_image(self, width, height, border_color):
        """创建边框颜色图像"""
        color_map = {
            "white": (255, 255, 255, 255),
            "black": (0, 0, 0, 255),
            "gray": (128, 128, 128, 255)
        }
        
        color = color_map[border_color]
        border_img = Image.new('RGBA', (width, height), color)
        return border_img

NODE_CLASS_MAPPINGS = {
    "MaskWhiteBorder": MaskWhiteBorder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskWhiteBorder": "Mask白边处理",
}