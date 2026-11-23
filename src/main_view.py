"""ClipOCR 主窗口 — 粘贴板查看 + 文字编辑 + 图片 OCR 视图。"""
from __future__ import annotations

import io
import threading
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageGrab, ImageTk

from ocr_engine import OcrWord, engine
from overlay_widget import ImageOverlay


class MainView(tk.Toplevel):
    def __init__(self, master: tk.Tk, clipboard_getter):
        super().__init__(master)
        self._get_clipboard = clipboard_getter

        self.title("ClipOCR")
        self.geometry("900x600")
        self.minsize(600, 400)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.bind("<Escape>", lambda _e: self.withdraw())

        # --- toolbar ---
        toolbar = tk.Frame(self, bg="#f0f0f0")
        toolbar.pack(fill=tk.X, side=tk.TOP)
        tk.Button(toolbar, text="粘贴", command=self._on_paste, padx=12).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="复制全部", command=self._on_copy_all, padx=12).pack(side=tk.LEFT, padx=0, pady=4)
        tk.Button(toolbar, text="OCR 识别", command=self._on_ocr, padx=12).pack(side=tk.LEFT, padx=4, pady=4)
        self.status = tk.Label(toolbar, text="就绪", bg="#f0f0f0", anchor="w")
        self.status.pack(side=tk.LEFT, padx=12)

        # --- body ---
        self.body = tk.Frame(self)
        self.body.pack(fill=tk.BOTH, expand=True)

        # 文字编辑区
        self.text = tk.Text(self.body, wrap=tk.WORD, font=("Microsoft YaHei", 12), bg="#1e1e23", fg="#eaeaea", insertbackground="#fff")
        self.scrollbar = tk.Scrollbar(self.body, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)
        self.text.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 图片视图（按需创建）
        self.overlay: ImageOverlay | None = None
        self._current_image: Image.Image | None = None
        self._current_words: list[OcrWord] = []

    # --- clipboard actions ------------------------------------------------

    def load_clipboard(self) -> None:
        """热键触发：抓当前粘贴板并展示。"""
        # 优先图片
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            self._show_image(img)
            self._set_status("已加载粘贴板图片，点击「OCR 识别」处理")
            return
        # 其次文本
        try:
            text = self._get_clipboard()
        except tk.TclError:
            text = ""
        self._show_text(text or "")
        if text:
            self._set_status("已加载粘贴板文字")
        else:
            self._set_status("粘贴板为空或含不支持的类型")

    def _on_paste(self) -> None:
        self.load_clipboard()

    def _on_copy_all(self) -> None:
        content = self.text.get("1.0", tk.END).strip()
        if not content:
            self._set_status("没有可复制的内容")
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        self._set_status("已复制全部文字")

    # --- display switching -----------------------------------------------

    def _show_text(self, text: str) -> None:
        if self.overlay is not None:
            self.overlay.destroy()
            self.overlay = None
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", text)

    def _show_image(self, img: Image.Image) -> None:
        if self.overlay is not None:
            self.overlay.destroy()
        self.text.pack_forget()
        self.scrollbar.pack_forget()
        self._current_image = img
        self._current_words = []
        self.overlay = ImageOverlay(self.body, image=img, words=[])
        self.overlay.pack(fill=tk.BOTH, expand=True)

    # --- OCR --------------------------------------------------------------

    def _on_ocr(self) -> None:
        if self.overlay is None or self._current_image is None:
            self._set_status("当前没有可识别的图片 — 先从粘贴板粘贴一张图片")
            return
        self._set_status("识别中…")
        threading.Thread(target=self._ocr_worker, daemon=True).start()

    def _ocr_worker(self) -> None:
        try:
            words = engine.recognize(self._current_image)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"识别失败: {exc}")
            return
        self._current_words = words
        self.after(0, self._apply_ocr_result)

    def _apply_ocr_result(self) -> None:
        if self.overlay is None:
            return
        self.overlay.destroy()
        self.overlay = ImageOverlay(self.body, image=self._current_image, words=self._current_words)
        self.overlay.pack(fill=tk.BOTH, expand=True)
        self._set_status(f"识别完成，共 {len(self._current_words)} 块文字（可在图片上划选复制）")

    # --- helpers ----------------------------------------------------------

    def _set_status(self, msg: str) -> None:
        try:
            self.status.configure(text=msg)
        except tk.TclError:
            pass

    @staticmethod
    def _image_to_bytes(img: Image.Image) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


def dummy_clipboard_get() -> str:
    return ""
