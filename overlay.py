"""永遠置頂、可拖曳的聊天式字幕面板。"""

from __future__ import annotations

import ctypes
import queue
import tkinter as tk
from collections import deque

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080
BOX_BG = "#000000"
PANEL_WIDTH = 900
PANEL_HEIGHT = 440
HISTORY_LIMIT = 10


class SubtitleOverlay:
    """
    text_queue: 主程式把 (原文, 中文) 丟進來。
    show_original: 要不要同時顯示原文。
    """

    def __init__(
        self,
        root: tk.Tk,
        text_queue: queue.Queue,
        show_original: tk.BooleanVar,
        font_size: tk.IntVar,
    ):
        self.root = root
        self.text_queue = text_queue
        self.show_original = show_original
        self.font_size = font_size
        self.history: deque[tuple[str, str]] = deque(maxlen=HISTORY_LIMIT)
        self._drag_x = 0
        self._drag_y = 0

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=BOX_BG, highlightbackground="#555555", highlightthickness=1)

        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        width = min(PANEL_WIDTH, screen_w - 40)
        height = min(PANEL_HEIGHT, screen_h - 80)
        x = max(20, (screen_w - width) // 2)
        y = max(20, screen_h - height - 50)
        self.win.geometry(f"{width}x{height}+{x}+{y}")

        self.header = tk.Label(
            self.win,
            text="上下文即時字幕　｜　按住此處拖曳",
            fg="#FFFFFF",
            bg="#202020",
            font=("Microsoft JhengHei", 12, "bold"),
            anchor="w",
            padx=12,
            pady=8,
        )
        self.header.pack(fill="x")

        self.chat = tk.Text(
            self.win,
            bg=BOX_BG,
            fg="#FFFFFF",
            relief="flat",
            borderwidth=0,
            padx=16,
            pady=10,
            wrap="word",
            cursor="arrow",
            state="disabled",
        )
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_configure(
            "original",
            foreground="#BDBDBD",
            spacing1=8,
            font=("Segoe UI", max(11, font_size.get() - 12)),
        )
        self.chat.tag_configure(
            "chinese",
            foreground="#FFFFFF",
            spacing1=2,
            spacing3=8,
            font=("Microsoft JhengHei", font_size.get(), "bold"),
        )
        self.chat.tag_configure(
            "waiting",
            foreground="#AAAAAA",
            justify="center",
            font=("Microsoft JhengHei", 16),
        )

        for widget in (self.win, self.header, self.chat):
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)

        self.win.update_idletasks()
        self._apply_window_style()
        self.show_original.trace_add("write", lambda *_: self._render())
        self.font_size.trace_add("write", lambda *_: self._render())
        self._render()
        self._poll()

    def _apply_window_style(self) -> None:
        inner = self.win.winfo_id()
        hwnd = ctypes.windll.user32.GetParent(inner) or inner
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def _start_drag(self, event) -> None:
        self._drag_x = event.x_root - self.win.winfo_x()
        self._drag_y = event.y_root - self.win.winfo_y()

    def _on_drag(self, event) -> None:
        self.win.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def clear(self) -> None:
        self.history.clear()
        self._render()

    def _render(self) -> None:
        size = self.font_size.get()
        self.chat.tag_configure(
            "original", font=("Segoe UI", max(11, size - 12))
        )
        self.chat.tag_configure(
            "chinese", font=("Microsoft JhengHei", size, "bold")
        )
        self.chat.config(state="normal")
        self.chat.delete("1.0", "end")

        if not self.history:
            self.chat.insert("end", "\n等待影片聲音…", "waiting")
        else:
            for original, chinese in self.history:
                if self.show_original.get():
                    self.chat.insert("end", f"原文　{original}\n", "original")
                self.chat.insert("end", f"繁中　{chinese or original}\n", "chinese")

        self.chat.config(state="disabled")
        self.chat.see("end")

    def _poll(self) -> None:
        changed = False
        while True:
            try:
                self.history.append(self.text_queue.get_nowait())
                changed = True
            except queue.Empty:
                break
        if changed:
            self._render()
        self.root.after(120, self._poll)
