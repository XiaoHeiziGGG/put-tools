# Put-Tools for ComfyUI

🎨 **ComfyUI 异形图像处理工具集** - 专业的非矩形区域图像处理解决方案

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Compatible-green.svg)](https://github.com/comfyanonymous/ComfyUI)

## 📋 目录

- [功能特性](#功能特性)
- [安装方法](#安装方法)
- [节点说明](#节点说明)
- [使用示例](#使用示例)
- [系统要求](#系统要求)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)
- [更新日志](#更新日志)
- [许可证](#许可证)

## ✨ 功能特性
<img width="1848" height="1085" alt="1" src="https://github.com/user-attachments/assets/77275115-de62-47a7-a1f0-60546668935f" />

### 🖼️ IrregularCropper - 异形图像裁剪
- **交互式界面**：直接在ComfyUI前端绘制裁剪区域
- **双重模式**：支持自由绘制和多边形选择
- **智能控制**：集成seed机制，支持固定/随机模式
- **高性能**：优化的内存管理，避免浏览器崩溃
- **平滑边缘**：无锯齿边缘处理
- **多种填充**：透明、黑色、白色、模糊背景

### 🎯 MaskWhiteBorder - 智能白边生成
- **自动裁剪**：根据mask自动识别异形区域
- **白边效果**：为异形物体添加可调节的白边
- **透明背景**：生成透明底的专业图像
- **精确控制**：可调节边框宽度、颜色、透明度

## 🛠️ 安装方法

### 方法一：Git Clone（推荐）
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/your-username/put-tools.git
```

### 方法二：手动下载
1. 下载本项目的ZIP文件
2. 解压到 `ComfyUI/custom_nodes/put-tools/`
3. 确保文件夹结构正确

### 方法三：ComfyUI Manager
如果已收录到ComfyUI Manager，可直接搜索"Put-Tools"安装

### 依赖安装
```bash
cd ComfyUI/custom_nodes/put-tools
pip install -r requirements.txt
```

## 📖 节点说明

### IrregularCropper

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| image | IMAGE | - | 输入图像 |
| crop_mode | 选择 | polygon | 裁剪模式：free_draw(自由绘制) / polygon(多边形) |
| background_fill | 选择 | transparent | 背景填充：transparent/black/white/blur |
| edge_smooth | INT | 0 | 边缘平滑程度 (0-20) |
| auto_crop | BOOLEAN | True | 是否自动裁剪到最小边界 |
| crop_padding | INT | 10 | 裁剪边距 (0-100) |
| seed | INT | 0 | 随机种子，控制界面状态 |
| control | 选择 | fixed | fixed(固定)/randomize(随机) |

**使用方法：**
1. 连接图像输入
2. 选择裁剪模式
3. 执行节点，会弹出交互界面
4. 在图像上绘制想要的区域
5. 完成绘制后关闭对话框
6. 设置control为"fixed"锁定结果

### MaskWhiteBorder

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| image | IMAGE | - | 输入图像 |
| mask | MASK | - | 输入遮罩 |
| border_width | INT | 20 | 白边宽度 (0-200) |
| border_color | 选择 | white | 边框颜色：white/black/gray |
| auto_crop | BOOLEAN | True | 是否自动裁剪 |
| crop_padding | INT | 10 | 裁剪边距 |

**使用方法：**
1. 准备图像和对应的mask
2. 连接到节点输入
3. 调整白边参数
4. 执行获得带白边的透明底图像

## 🎯 使用示例

### 示例1：人物异形裁剪
```
LoadImage → IrregularCropper → SaveImage
```
1. 加载人物图像
2. 使用IrregularCropper，选择polygon模式
3. 在弹出界面中点击勾勒人物轮廓
4. 得到透明底的人物图像

### 示例2：物体白边效果
```
LoadImage → ObjectDetection → MaskWhiteBorder → SaveImage
```
1. 加载物体图像
2. 生成物体的mask（可用其他节点）
3. 使用MaskWhiteBorder添加白边
4. 保存带白边的透明底图像

### 示例3：复合工作流
```
LoadImage → IrregularCropper → MaskFromImage → MaskWhiteBorder → CompositeImage
```
1. 异形裁剪获得主体
2. 从裁剪结果生成mask  
3. 添加白边效果
4. 与其他图像合成

## 💻 系统要求

### 最低要求
- **操作系统**：Windows 10+, macOS 10.14+, Linux
- **Python**：3.8+
- **ComfyUI**：最新版本
- **内存**：8GB RAM
- **显卡**：支持CUDA的NVIDIA显卡（推荐）

### 推荐配置
- **内存**：16GB+ RAM
- **显卡**：RTX 3060+
- **存储**：SSD硬盘

### 浏览器要求
- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

## 🔧 故障排除

### 常见问题

**Q: 节点无法找到？**
A: 确保文件夹名为`put-tools`且放在`custom_nodes`目录下，重启ComfyUI

**Q: 交互界面无法打开？**
A: 检查浏览器控制台错误，确保JavaScript文件加载正常

**Q: 浏览器崩溃？**
A: 降低图像分辨率，关闭其他标签页，确保系统内存充足

**Q: 边缘有锯齿？**
A: 增加edge_smooth参数值，或使用polygon模式

**Q: 依赖安装失败？**
A: 使用conda环境或虚拟环境，单独安装每个依赖包

### 性能优化

1. **内存优化**：处理大图时建议分批处理
2. **显卡优化**：确保CUDA正确安装和配置
3. **浏览器优化**：关闭不必要的标签页和扩展


如果你觉得有用可以请我喝杯咖啡：
![78aecc22d868515291c1cb6f156a45d](https://github.com/user-attachments/assets/27bea7c8-7e63-4a68-8928-b94bb51efa95)

