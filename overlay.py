"""永遠置頂、可點穿的字幕層，蓋在螢幕下方。"""

from __future__ import annotations

import ctypes
import queue
import tkinter as tk

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
TRANSPARENT_KEY = "#010101"


class SubtitleOverlay:
    """
    text_queue: 主程式把 (原文, 中文) 丟進來。
    show_original: 要不要同時顯示原文。
    """

    def __init__(self, root: tk.Tk, text_queue: queue.Queue, show_original: tk.BooleanVar, font_size: tk.IntVar):
        self.root = root
        self.text_queue = text_queue
        self.show_original = show_original
        self.font_size = font_size

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", TRANSPARENT_KEY)
        self.win.configure(bg=TRANSPARENT_KEY)

        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        height = 180
        self.win.geometry(f"{screen_w}x{height}+0+{screen_h - height - 40}")

        self.zh_label = tk.Label(
            self.win,
            text="等待影片聲音…",
            fg="#FFFFFF",
            bg=TRANSPARENT_KEY,
            font=("Microsoft JhengHei", font_size.get(), "bold"),
            wraplength=screen_w - 80,
            justify="center",
        )
        self.zh_label.pack(side="bottom", pady=(0, 12))

        self.src_label = tk.Label(
            self.win,
            text="",
            fg="#DDDDDD",
            bg=TRANSPARENT_KEY,
            font=("Segoe UI", max(12, font_size.get() - 10)),
            wraplength=screen_w - 80,
            justify="center",
        )
        self.src_label.pack(side="bottom")

        self.win.update_idletasks()
        self._enable_clickthrough()
        self._poll()

    def _enable_clickthrough(self) -> None:
        inner = self.win.winfo_id()
        hwnd = ctypes.windll.user32.GetParent(inner) or inner
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def _poll(self) -> None:
        latest = None
        while True:
            try:
                latest = self.text_queue.get_nowait()
            except queue.Empty:
                break
        if latest is not None:
            original, chinese = latest
            size = self.font_size.get()
            self.zh_label.config(
                text=chinese or original,
                font=("Microsoft JhengHei", size, "bold"),
            )
            if self.show_original.get() and original:
                self.src_label.config(
                    text=original,
                    font=("Segoe UI", max(12, size - 10)),
                )
            else:
                self.src_label.config(text="")
        self.root.after(120, self._poll)
