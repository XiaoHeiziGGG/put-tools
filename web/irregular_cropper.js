import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// 全局变量，避免重复创建
let irregularCropperModal = null;
let irregularCropperStyle = null;

// 安全创建模态窗口
function getOrCreateIrregularCropperModal() {
    if (irregularCropperModal && document.body.contains(irregularCropperModal)) {
        return irregularCropperModal;
    }

    // 清理旧的模态窗口
    const existingModal = document.getElementById("irregular-cropper-modal");
    if (existingModal) {
        existingModal.remove();
    }

    const modal = document.createElement("dialog");
    modal.id = "irregular-cropper-modal";
    modal.innerHTML = `
        <div class="irregular-cropper-container">
            <div class="irregular-cropper-header">
                <h3>异形图像裁剪</h3>
                <div class="mode-selector">
                    <label>
                        <input type="radio" name="drawing-mode" value="polygon" checked>
                        多边形选择
                    </label>
                    <label>
                        <input type="radio" name="drawing-mode" value="free_draw">
                        自由绘制
                    </label>
                </div>
                <button class="close-button">×</button>
            </div>
            <div class="irregular-cropper-content">
                <div class="irregular-cropper-wrapper">
                    <canvas id="irregular-crop-canvas"></canvas>
                    <div class="drawing-controls">
                        <button id="undo-point">撤销点</button>
                        <button id="clear-path">清除路径</button>
                        <button id="close-path">闭合路径</button>
                    </div>
                </div>
                <div class="irregular-cropper-controls">
                    <button id="apply-irregular-crop">应用裁剪</button>
                    <button id="cancel-irregular-crop">取消</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    irregularCropperModal = modal;
    return modal;
}

// 安全添加样式
function ensureIrregularCropperStyles() {
    if (irregularCropperStyle && document.head.contains(irregularCropperStyle)) {
        return;
    }

    // 清理旧样式
    const existingStyle = document.getElementById("irregular-cropper-styles");
    if (existingStyle) {
        existingStyle.remove();
    }

    const style = document.createElement("style");
    style.id = "irregular-cropper-styles";
    style.textContent = `
        #irregular-cropper-modal {
            border: none;
            border-radius: 8px;
            padding: 0;
            background: #2a2a2a;
            max-width: 95vw;
            max-height: 95vh;
        }
        
        .irregular-cropper-container {
            width: fit-content;
            height: fit-content;
            min-width: 500px;
            min-height: 400px;
            display: flex;
            flex-direction: column;
        }
        
        .irregular-cropper-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: #333;
            border-bottom: 1px solid #444;
        }
        
        .irregular-cropper-header h3 {
            margin: 0;
            color: #fff;
        }
        
        .mode-selector {
            display: flex;
            gap: 15px;
        }
        
        .mode-selector label {
            color: #fff;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .mode-selector input[type="radio"] {
            margin: 0;
        }
        
        .close-button {
            background: none;
            border: none;
            color: #fff;
            font-size: 24px;
            cursor: pointer;
        }
        
        .irregular-cropper-content {
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            overflow: auto;
        }
        
        .irregular-cropper-wrapper {
            position: relative;
            background: #1a1a1a;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
        }
        
        #irregular-crop-canvas {
            max-width: 100%;
            max-height: 70vh;
            object-fit: contain;
            cursor: crosshair;
            border: 1px solid #555;
        }
        
        .drawing-controls {
            display: flex;
            gap: 10px;
        }
        
        .drawing-controls button {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            background: #555;
            color: white;
            cursor: pointer;
            font-size: 12px;
        }
        
        .drawing-controls button:hover {
            background: #666;
        }
        
        .irregular-cropper-controls {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        
        .irregular-cropper-controls button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        
        #apply-irregular-crop {
            background: #2a8af6;
            color: white;
        }
        
        #cancel-irregular-crop {
            background: #666;
            color: white;
        }
        
        .irregular-cropper-controls button:hover {
            opacity: 0.9;
        }
    `;
    document.head.appendChild(style);
    irregularCropperStyle = style;
}

// 异形裁剪功能类
class IrregularCropper {
    constructor() {
        this.modal = null;
        this.canvas = null;
        this.ctx = null;

        this.pathPoints = [];
        this.isDrawing = false;
        this.drawingMode = "polygon";
        this.currentPath = [];
        this.pathClosed = false;
        this.originalImageData = null;

        // 添加内存管理
        this.maxImageSize = 4096 * 4096;
        this.isInitialized = false;
    }

    initialize() {
        if (this.isInitialized) {
            return;
        }

        ensureIrregularCropperStyles();
        this.modal = getOrCreateIrregularCropperModal();
        this.canvas = this.modal.querySelector("#irregular-crop-canvas");
        this.ctx = this.canvas.getContext("2d");

        // 启用抗锯齿 - 这是关键修复
        this.ctx.imageSmoothingEnabled = true;
        this.ctx.imageSmoothingQuality = 'high';

        this.setupEventListeners();
        this.isInitialized = true;
    }

    setupEventListeners() {
        if (this.eventListenersAdded) {
            return;
        }

        const closeButton = this.modal.querySelector(".close-button");
        closeButton.addEventListener("click", () => this.cleanupAndClose(true));

        const cancelButton = this.modal.querySelector("#cancel-irregular-crop");
        cancelButton.addEventListener("click", () => this.cleanupAndClose(true));

        const applyButton = this.modal.querySelector("#apply-irregular-crop");
        applyButton.addEventListener("click", () => this.applyIrregularCrop());

        const modeInputs = this.modal.querySelectorAll('input[name="drawing-mode"]');
        modeInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.drawingMode = e.target.value;
                this.clearPath();
            });
        });

        const undoButton = this.modal.querySelector("#undo-point");
        undoButton.addEventListener("click", () => this.undoLastPoint());

        const clearButton = this.modal.querySelector("#clear-path");
        clearButton.addEventListener("click", () => this.clearPath());

        const closePathButton = this.modal.querySelector("#close-path");
        closePathButton.addEventListener("click", () => this.closePath());

        this.modal.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                this.cleanupAndClose(true);
            }
        });

        // 画布事件
        this.canvas.addEventListener("mousedown", (e) => this.handleMouseDown(e), { passive: false });
        this.canvas.addEventListener("mousemove", (e) => this.handleMouseMove(e), { passive: true });
        this.canvas.addEventListener("mouseup", (e) => this.handleMouseUp(e), { passive: true });
        this.canvas.addEventListener("dblclick", (e) => this.handleDoubleClick(e), { passive: false });
        this.canvas.addEventListener("contextmenu", (e) => e.preventDefault(), { passive: false });

        this.eventListenersAdded = true;
    }

    getCanvasCoordinates(e) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;

        // 保持坐标精度，但四舍五入到像素
        return {
            x: Math.round((e.clientX - rect.left) * scaleX),
            y: Math.round((e.clientY - rect.top) * scaleY)
        };
    }

    handleMouseDown(e) {
        const coords = this.getCanvasCoordinates(e);

        if (this.drawingMode === "polygon") {
            if (!this.pathClosed) {
                this.pathPoints.push(coords);
                this.redrawCanvas();
            }
        } else if (this.drawingMode === "free_draw") {
            this.isDrawing = true;
            this.currentPath = [coords];
        }
    }

    handleMouseMove(e) {
        if (this.drawingMode === "free_draw" && this.isDrawing) {
            const coords = this.getCanvasCoordinates(e);
            // 限制路径点数量防止内存溢出，但保持足够的精度
            if (this.currentPath.length < 8000) {
                this.currentPath.push(coords);
                // 适当的重绘频率
                if (this.currentPath.length % 4 === 0) {
                    this.redrawCanvas();
                }
            }
        }
    }

    handleMouseUp(e) {
        if (this.drawingMode === "free_draw" && this.isDrawing) {
            this.isDrawing = false;
            // 温和的路径简化，保持平滑度
            this.pathPoints = this.pathPoints.concat(this.simplifyPath(this.currentPath, 1.5));
            this.currentPath = [];
            this.redrawCanvas();
        }
    }

    handleDoubleClick(e) {
        if (this.drawingMode === "polygon" && this.pathPoints.length >= 3) {
            this.closePath();
        }
    }

    // 改进的路径简化算法 - 保持平滑度
    simplifyPath(path, tolerance = 1.5) {
        if (path.length < 3) return path;

        const simplified = [path[0]];

        for (let i = 1; i < path.length - 1; i++) {
            const prev = path[i - 1];
            const curr = path[i];
            const next = path[i + 1];

            // 计算点到直线的距离
            const dist = this.pointToLineDistance(curr, prev, next);
            if (dist > tolerance) {
                simplified.push(curr);
            }
        }

        simplified.push(path[path.length - 1]);
        return simplified;
    }

    pointToLineDistance(point, lineStart, lineEnd) {
        const A = point.x - lineStart.x;
        const B = point.y - lineStart.y;
        const C = lineEnd.x - lineStart.x;
        const D = lineEnd.y - lineStart.y;

        const dot = A * C + B * D;
        const lenSq = C * C + D * D;

        if (lenSq === 0) return Math.sqrt(A * A + B * B);

        let t = dot / lenSq;
        t = Math.max(0, Math.min(1, t));

        const projX = lineStart.x + t * C;
        const projY = lineStart.y + t * D;

        const dx = point.x - projX;
        const dy = point.y - projY;

        return Math.sqrt(dx * dx + dy * dy);
    }

    undoLastPoint() {
        if (this.pathPoints.length > 0) {
            this.pathPoints.pop();
            this.pathClosed = false;
            this.redrawCanvas();
        }
    }

    clearPath() {
        this.pathPoints = [];
        this.currentPath = [];
        this.pathClosed = false;
        this.redrawCanvas();
    }

    closePath() {
        if (this.pathPoints.length >= 3) {
            this.pathClosed = true;
            this.redrawCanvas();
        }
    }

    redrawCanvas() {
        if (this.redrawRequested) return;
        this.redrawRequested = true;

        requestAnimationFrame(() => {
            this.performRedraw();
            this.redrawRequested = false;
        });
    }

    performRedraw() {
        // 清除画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 重新绘制原始图像
        if (this.originalImageData) {
            this.ctx.putImageData(this.originalImageData, 0, 0);
        }

        // 设置抗锯齿绘制参数
        this.ctx.imageSmoothingEnabled = true;
        this.ctx.imageSmoothingQuality = 'high';
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        // 绘制路径
        if (this.pathPoints.length > 0) {
            this.ctx.strokeStyle = "#00ff00";
            this.ctx.fillStyle = "rgba(0, 255, 0, 0.2)";
            this.ctx.lineWidth = 2;

            this.ctx.beginPath();
            this.ctx.moveTo(this.pathPoints[0].x, this.pathPoints[0].y);

            for (let i = 1; i < this.pathPoints.length; i++) {
                this.ctx.lineTo(this.pathPoints[i].x, this.pathPoints[i].y);
            }

            if (this.pathClosed || (this.pathPoints.length >= 3 && this.drawingMode === "free_draw")) {
                this.ctx.closePath();
                this.ctx.fill();
            }

            this.ctx.stroke();

            // 绘制顶点（仅在多边形模式下且点数不多时）
            if (this.drawingMode === "polygon" && this.pathPoints.length < 100) {
                this.ctx.fillStyle = "#ff0000";
                for (const point of this.pathPoints) {
                    this.ctx.beginPath();
                    this.ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
                    this.ctx.fill();
                }
            }
        }

        // 绘制当前绘制路径
        if (this.currentPath.length > 0) {
            this.ctx.strokeStyle = "#ffff00";
            this.ctx.lineWidth = 2;
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';

            this.ctx.beginPath();
            this.ctx.moveTo(this.currentPath[0].x, this.currentPath[0].y);

            for (let i = 1; i < this.currentPath.length; i++) {
                this.ctx.lineTo(this.currentPath[i].x, this.currentPath[i].y);
            }

            this.ctx.stroke();
        }
    }

    async applyIrregularCrop() {
        if (this.pathPoints.length < 3) {
            alert("需要至少3个点来形成选择区域");
            return;
        }

        try {
            const response = await api.fetchApi("/irregular_cropper/apply", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    node_id: this.currentNodeId,
                    path_points: this.pathPoints.slice(0, 2000), // 适当的点数限制
                    image_width: this.canvas.width,
                    image_height: this.canvas.height,
                    drawing_mode: this.drawingMode
                })
            });

            const result = await response.json();
            this.cleanupAndClose();

        } catch (error) {
            console.error("异形裁剪操作失败:", error);
            alert("裁剪操作失败: " + error.message);
        }
    }

    async cleanupAndClose(cancelled = false) {
        // 发送取消信号
        if (cancelled && this.currentNodeId) {
            try {
                await api.fetchApi("/irregular_cropper/cancel", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        node_id: this.currentNodeId
                    })
                });
            } catch (error) {
                console.error("发送取消信号失败:", error);
            }
        }

        // 清理内存
        this.pathPoints = [];
        this.currentPath = [];
        this.pathClosed = false;
        this.isDrawing = false;
        this.originalImageData = null;

        // 清理画布
        if (this.ctx && this.canvas) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }

        // 关闭窗口
        if (this.modal) {
            this.modal.close();
        }
    }

    show(nodeId, imageData, config) {
        this.initialize();
        this.currentNodeId = nodeId;
        this.config = config;

        // 设置模式
        const modeInput = this.modal.querySelector(`input[value="${config.crop_mode}"]`);
        if (modeInput) {
            modeInput.checked = true;
            this.drawingMode = config.crop_mode;
        }

        const img = new Image();
        img.onload = () => {
            const imageSize = img.width * img.height;
            if (imageSize > this.maxImageSize) {
                alert(`图像过大 (${img.width}x${img.height})，可能导致浏览器崩溃。请使用较小的图像。`);
                return;
            }

            this.canvas.width = img.width;
            this.canvas.height = img.height;

            // 启用高质量绘制
            this.ctx.imageSmoothingEnabled = true;
            this.ctx.imageSmoothingQuality = 'high';
            this.ctx.drawImage(img, 0, 0);

            // 保存原始图像数据
            this.originalImageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);

            this.modal.showModal();
        };

        img.onerror = (error) => {
            console.error("图像加载失败:", error);
            alert("图像加载失败");
        };

        img.src = imageData;
    }
}

// 全局实例
let globalIrregularCropper = null;

// 注册节点扩展
app.registerExtension({
    name: "Comfy.IrregularCropper",
    async setup() {
        globalIrregularCropper = new IrregularCropper();

        api.addEventListener("irregular_cropper_update", ({ detail }) => {
            const { node_id, image_data, ...config } = detail;
            const node = app.graph.getNodeById(node_id);
            if (node) {
                globalIrregularCropper.show(node_id, image_data, config);
            }
        });
    },

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "IrregularCropper") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }

                this.addWidget("text", "使用说明", "多边形模式：点击添加顶点，双击闭合路径\n自由绘制模式：按住鼠标拖拽绘制选择区域", null, {
                    multiline: true,
                    serialize: false
                });

                // Seed控制逻辑
                const seedWidget = this.addWidget("number", "seed", 0, (value) => {
                    this.seed = value;
                }, {
                    min: 0,
                    max: Number.MAX_SAFE_INTEGER,
                    step: 1,
                    precision: 0
                });

                const seed_modeWidget = this.addWidget("combo", "seed_mode", "randomize", () => { }, {
                    values: ["fixed", "increment", "decrement", "randomize"],
                    serialize: false
                });

                seed_modeWidget.beforeQueued = () => {
                    const mode = seed_modeWidget.value;
                    let newValue = seedWidget.value;

                    if (mode === "randomize") {
                        newValue = Math.floor(Math.random() * Number.MAX_SAFE_INTEGER);
                    } else if (mode === "increment") {
                        newValue += 1;
                    } else if (mode === "decrement") {
                        newValue -= 1;
                    } else if (mode === "fixed") {
                        if (!this.hasFixedSeed) {
                            newValue = Math.floor(Math.random() * Number.MAX_SAFE_INTEGER);
                            this.hasFixedSeed = true;
                        }
                    }

                    seedWidget.value = newValue;
                    this.seed = newValue;
                };

                seed_modeWidget.callback = (value) => {
                    if (value !== "fixed") {
                        this.hasFixedSeed = false;
                    }
                };

                this.addWidget("button", "更新种子", null, () => {
                    const mode = seed_modeWidget.value;
                    let newValue = seedWidget.value;

                    if (mode === "randomize") {
                        newValue = Math.floor(Math.random() * Number.MAX_SAFE_INTEGER);
                    } else if (mode === "increment") {
                        newValue += 1;
                    } else if (mode === "decrement") {
                        newValue -= 1;
                    } else if (mode === "fixed") {
                        newValue = Math.floor(Math.random() * Number.MAX_SAFE_INTEGER);
                        this.hasFixedSeed = true;
                    }

                    seedWidget.value = newValue;
                    seedWidget.callback(newValue);
                });
            };
        }
    }
});