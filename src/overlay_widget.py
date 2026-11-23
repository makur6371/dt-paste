"""图片透明文本覆盖层 — 复刻 OCR.html 的核心逻辑到 tkinter Canvas。"""
from __future__ import annotations

import tkinter as tk
from typing import List

from PIL import Image, ImageTk

from ocr_engine import OcrWord


class ImageOverlay(tk.Frame):
    """左侧原图、右侧/覆盖层对齐透明文字的复合控件。"""

    def __init__(self, master, *args, image: Image.Image, words: List[OcrWord], **kwargs):
        super().__init__(master, *args, **kwargs)
        self._words = words
        self._image = image
        self._photo: ImageTk.PhotoImage

        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#2b2b2f")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._photo = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._photo)
        self.canvas.config(width=image.width, height=image.height)

        # 透明文字：用 0 宽度边框 + 让可选中的 Text 小部件覆盖
        self._render_overlays(image.width, image.height)

        self.bind("<Configure>", self._on_resize)

    # --- rendering -------------------------------------------------------

    def _render_overlays(self, disp_w: int, disp_h: int) -> None:
        nat_w, nat_h = self._image.size
        sx = disp_w / nat_w
        sy = disp_h / nat_h
        for w in self._words:
            x0 = w.x0 * sx
            y0 = w.y0 * sy
            x1 = w.x1 * sx
            y1 = w.y1 * sy
            height = max(y1 - y0, 1)
            font_size = max(int(height * 0.7), 6)
            label = tk.Label(
                self.canvas,
                text=w.text,
                font=("Microsoft YaHei", font_size),
                fg="transparent",
                bg="transparent",
                cursor="xterm",
            )
            # 让 label 的文字可被选区：设置 selectforeground/background 但由于是透明前景实际看不到
            label.bind("<Button-1>", lambda e, l=label: l.focus_set())
            label.bind("<Control-a>", lambda e, l=label: (l.focus_set(), l.select_range(0, tk.END)))
            self.canvas.create_window(x0, y0, anchor=tk.NW, width=max(x1 - x0, 1), height=height, window=label)

    def _on_resize(self, event: tk.Event) -> None:  # noqa: ARG002
        pass  # 简化实现：Canvas 固定尺寸 = 图片尺寸，窗口用滚动条
