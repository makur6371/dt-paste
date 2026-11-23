"""端侧 OCR 引擎，优先 PaddleOCR，回退 Tesseract。

PaddleOCR 3.7.x 的 rec_boxes / rec_texts / rec_scores 输出结构与旧版不同，
本模块显式读取新字段。
"""
from __future__ import annotations

import importlib
import shutil
from dataclasses import dataclass
from typing import List, Optional

from PIL import Image


@dataclass
class OcrWord:
    text: str
    x0: int
    y0: int
    x1: int
    y1: int


class OcrEngine:
    """惰性加载 OCR 后端；同一进程内复用一个 worker。"""

    def __init__(self):
        self._backend: Optional[object] = None
        self._backend_name: str = ""

    # --- public ----------------------------------------------------------

    @property
    def name(self) -> str:
        return self._backend_name or "未初始化"

    def is_ready(self) -> bool:
        return self._backend is not None

    def recognize(self, image: Image.Image) -> List[OcrWord]:
        if self._backend is None:
            self._load_backend()
        if self._backend is None:
            return []
        return self._dispatch(image)

    # --- backend bootstrapping ------------------------------------------

    def _load_backend(self) -> None:
        # 1) 尝试 PaddleOCR
        if importlib.util.find_spec("paddleocr") is not None:
            try:
                from paddleocr import PaddleOCR

                self._backend = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",
                    text_detection_model_dir=None,
                    text_recognition_model_dir=None,
                    # 禁用 mkldnn，规避部分 CPU 不支持 PIR/OneDNN 的问题
                    enable_mkldnn=False,
                )
                self._backend_name = "PaddleOCR"
                return
            except Exception as exc:  # noqa: BLE001
                print(f"[OCR] PaddleOCR 加载失败，尝试回退: {exc}")

        # 2) 回退 Tesseract（需要本体 + chi_sim 训练数据）
        if shutil.which("tesseract") is not None or importlib.util.find_spec("pytesseract") is not None:
            try:
                import pytesseract

                self._backend = pytesseract
                self._backend_name = "Tesseract"
                return
            except Exception as exc:  # noqa: BLE001
                print(f"[OCR] Tesseract 加载失败: {exc}")

        print("[OCR] 无可用的 OCR 后端，OCR 功能已禁用")

    def _dispatch(self, image: Image.Image) -> List[OcrWord]:
        if self._backend_name == "PaddleOCR":
            return self._run_paddle(image)
        if self._backend_name == "Tesseract":
            return self._run_tesseract(image)
        return []

    # --- Paddle ----------------------------------------------------------

    def _run_paddle(self, image: Image.Image) -> List[OcrWord]:
        import numpy as np

        # PaddleOCR 3.7 predict/ocr 返回 dict 列表；rec_boxes 是 (N,4) 的 [x0,y0,x1,y1]；rec_texts 是 (N,) 字符串
        result = self._backend.ocr(np.array(image))
        words: List[OcrWord] = []
        if not result or not isinstance(result[0], dict):
            return words
        page = result[0]
        boxes = page.get("rec_boxes")
        texts = page.get("rec_texts")
        if boxes is None or texts is None:
            return words
        boxes = np.asarray(boxes)
        for i, text in enumerate(texts):
            row = boxes[i]
            words.append(
                OcrWord(
                    text=str(text),
                    x0=int(row[0]),
                    y0=int(row[1]),
                    x1=int(row[2]),
                    y1=int(row[3]),
                )
            )
        return words

    # --- Tesseract -------------------------------------------------------

    def _run_tesseract(self, image: Image.Image) -> List[OcrWord]:
        data = self._backend.image_to_data(image, lang="chi_sim+eng", output_type=self._backend.Output.DICT)
        words: List[OcrWord] = []
        for i, text in enumerate(data["text"]):
            if not text or not text.strip():
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            words.append(OcrWord(text=text, x0=x, y0=y, x1=x + w, y1=y + h))
        return words


# 全局单例
engine = OcrEngine()
