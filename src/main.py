"""带控制台输出的主入口，用于打包为可执行程序。"""
from __future__ import annotations

import os
import sys
import threading
from typing import List, Optional

# 启动日志 — 写到 TEMP 目录，方便排查打包后启动失败
_log_path = os.path.join(os.environ.get("TEMP", "."), "clipocr_debug.log")
with open(_log_path, "a", encoding="utf-8") as _lf:
    _lf.write(f"[boot] python={sys.executable} frozen={getattr(sys,'frozen',False)} _MEIPASS={getattr(sys,'_MEIPASS','')}\n")

try:
    import pystray
    from PIL import Image, ImageDraw
    with open(_log_path, "a", encoding="utf-8") as _lf:
        _lf.write("[boot] imports ok\n")
except BaseException as _imp_exc:  # noqa: BLE001
    import traceback
    with open(_log_path, "a", encoding="utf-8") as _lf:
        _lf.write(f"[boot] IMPORT FAIL: {_imp_exc}\n{traceback.format_exc()}\n")
    raise

# 确保 PaddleOCR 路径可被找到
if getattr(sys, "frozen", False):
    # PyInstaller 打包后运行在 _MEIPASS 下
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))


def _build_icon(size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([4, 4, size - 4, size - 4], radius=12, fill=(0, 122, 255, 255))
    draw.text((size // 2, size // 2), "C", fill="white", anchor="mm")
    return img


class ClipboardApp:
    def __init__(self):
        self._history: List[str] = []
        self._view = None
        self._root = None
        self._tray = pystray.Icon(
            "clipocr",
            _build_icon(),
            menu=pystray.Menu(
                pystray.MenuItem("打开/粘贴 (Ctrl+Shift+V)", self._open_view, default=True),
                pystray.MenuItem("退出", self._on_exit),
            ),
        )
        with open(_log_path, "a", encoding="utf-8") as _lf:
            _lf.write("[app] ClipboardApp constructed\n")

    def run(self) -> None:
        from pynput import keyboard

        hotkey = keyboard.HotKey(keyboard.HotKey.parse("<ctrl>+<shift>+v"), self._open_view)
        listener = keyboard.Listener(on_press=hotkey.press, on_release=hotkey.release)
        listener.start()
        with open(_log_path, "a", encoding="utf-8") as _lf:
            _lf.write("[app] pynput listener started, starting tray.run()\n")

        self._tray.run()
        with open(_log_path, "a", encoding="utf-8") as _lf:
            _lf.write("[app] tray.run() returned\n")

    def _open_view(self) -> None:
        with open(_log_path, "a", encoding="utf-8") as _lf:
            _lf.write("[app] _open_view called\n")

        import tkinter as tk
        from main_view import MainView

        if self._root is None:
            self._root = tk.Tk()
            self._root.withdraw()
            with open(_log_path, "a", encoding="utf-8") as _lf:
                _lf.write("[app] tk root created\n")

        if self._view is None:
            self._view = MainView(self._root, self._root.clipboard_get)
            with open(_log_path, "a", encoding="utf-8") as _lf:
                _lf.write("[app] MainView created\n")
        try:
            self._view.deiconify()
            self._view.lift()
            self._view.focus_force()
            with open(_log_path, "a", encoding="utf-8") as _lf:
                _lf.write("[app] view deiconified\n")
        except tk.TclError:
            self._view = MainView(self._root, self._root.clipboard_get)
            with open(_log_path, "a", encoding="utf-8") as _lf:
                _lf.write("[app] view recreated after TclError\n")

    def _on_exit(self, *_args) -> None:
        try:
            self._tray.stop()
        except Exception:
            pass
        if self._root is not None:
            try:
                self._root.destroy()
            except Exception:
                pass


def main() -> None:
    import os
    log_path = os.path.join(os.environ.get("TEMP", "."), "clipocr_debug.log")
    with open(log_path, "a", encoding="utf-8") as lf:
        lf.write("[main] starting\n")
        try:
            app = ClipboardApp()
            lf.write("[main] app created, calling run()\n")
            lf.flush()
            app.run()
            lf.write("[main] run() returned\n")
        except SystemExit:
            raise
        except BaseException as exc:  # noqa: BLE001
            import traceback
            lf.write(f"[main] UNCAUGHT: {exc}\n")
            lf.write(traceback.format_exc())
            lf.flush()
            raise


if __name__ == "__main__":
    main()
