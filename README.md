# ClipOCR — 超轻量桌面粘贴板 + 端侧 OCR 工具

## 核心特性
- 全局热键 `Ctrl+Shift+V` 唤醒主窗口，直接查看/编辑粘贴板文字或 OCR 识别的图片
- 托盘静默运行，历史记录常驻，可直接从托盘菜单快速复制最近条目
- 端侧 OCR 支持中英文混合，透明文本覆盖层让图上文字可直接划选复制
- 单文件可执行程序，体积 < 50MB

## 布局
- `src/main.py`          入口：托盘 + 热键 + 主窗口调度
- `src/ocr_engine.py`    OCR 引擎封装（PaddleOCR 优先，回退 Tesseract）
- `src/overlay_widget.py` 图片透明文本覆盖层（复刻 OCR.html 的核心渲染逻辑）
- `assets/icon.ico`      托盘与程序图标
- `dist/`                打包输出目录

## 热键
- `Ctrl+Shift+V` : 唤醒主窗口并加载当前粘贴板内容
- `Esc`          : 主窗口隐藏不清空（下次唤醒保留上下文）

## 技术选型
- Python 3.10+
- tkinter (标准库) — UI
- pynput — 全局热键
- pystray + Pillow — 系统托盘
- paddleocr / pytesseract — 端侧 OCR
- pyinstaller — 打包

## 运行
```bash
pip install -r requirements.txt
python src/main.py
```

## 打包
```bash
pyinstaller build.spec --noconfirm
```
