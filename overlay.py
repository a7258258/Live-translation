"""永遠置頂、可拖曳的聊天式字幕視窗。"""

from __future__ import annotations

import ctypes
import queue
import tkinter as tk
from collections import deque

import theme

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080
PANEL_WIDTH = 940
PANEL_HEIGHT = 640
HISTORY_LIMIT = 10


class SubtitleOverlay:
    """
    text_queue: 主程式把 (原文, 中文) 丟進來。
    show_original: 要不要同時顯示原文。
    controls: 主程式把控制項放進這一列，維持單一視窗。
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

        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(
            bg=theme.BG,
            highlightbackground=theme.BORDER,
            highlightthickness=1,
        )

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = min(PANEL_WIDTH, screen_w - 40)
        height = min(PANEL_HEIGHT, screen_h - 80)
        x = max(20, (screen_w - width) // 2)
        y = max(20, screen_h - height - 50)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        header = tk.Frame(self.root, bg=theme.HEADER)
        header.pack(fill="x")

        self.status_dot = tk.Canvas(
            header,
            width=10,
            height=10,
            bg=theme.HEADER,
            highlightthickness=0,
        )
        self._dot = self.status_dot.create_oval(1, 1, 9, 9, fill=theme.MUTED, outline="")
        self.status_dot.pack(side="left", padx=(14, 8))

        self.header = tk.Label(
            header,
            text="Live-translation",
            fg=theme.TEXT,
            bg=theme.HEADER,
            font=(theme.CJK_FONT, 11, "bold"),
            anchor="w",
        )
        self.header.pack(side="left", pady=10)

        self.hint = tk.Label(
            header,
            text="按住標題列拖曳",
            fg=theme.MUTED,
            bg=theme.HEADER,
            font=(theme.UI_FONT, 9),
        )
        self.hint.pack(side="left", padx=10)

        self.close_btn = tk.Label(
            header,
            text="✕",
            fg=theme.MUTED,
            bg=theme.HEADER,
            font=(theme.UI_FONT, 12),
            padx=14,
            pady=8,
            cursor="hand2",
        )
        self.close_btn.pack(side="right")
        self.close_btn.bind("<Button-1>", lambda _: self.root.destroy())
        self.close_btn.bind("<Enter>", lambda _: self.close_btn.config(fg=theme.DANGER))
        self.close_btn.bind("<Leave>", lambda _: self.close_btn.config(fg=theme.MUTED))

        tk.Frame(self.root, bg=theme.BORDER, height=1).pack(fill="x")

        self.controls = tk.Frame(self.root, bg=theme.PANEL)
        self.controls.pack(fill="x", side="bottom")
        tk.Frame(self.root, bg=theme.BORDER, height=1).pack(fill="x", side="bottom")

        chat_area = tk.Frame(self.root, bg=theme.BG)
        chat_area.pack(fill="both", expand=True)

        self.chat = tk.Text(
            chat_area,
            bg=theme.BG,
            fg=theme.TEXT,
            relief="flat",
            borderwidth=0,
            padx=18,
            pady=14,
            wrap="word",
            cursor="arrow",
            state="disabled",
            insertwidth=0,
            selectbackground=theme.BUBBLE,
        )
        self.chat.pack(side="left", fill="both", expand=True)

        self.chat.tag_configure(
            "original",
            foreground=theme.MUTED,
            lmargin1=4,
            lmargin2=4,
            spacing1=10,
            spacing3=2,
        )
        self.chat.tag_configure(
            "chinese",
            foreground=theme.TEXT,
            background=theme.BUBBLE,
            lmargin1=10,
            lmargin2=10,
            rmargin=10,
            spacing1=6,
            spacing3=6,
        )
        self.chat.tag_configure(
            "waiting",
            foreground=theme.MUTED,
            justify="center",
            font=(theme.CJK_FONT, 13),
            spacing1=24,
        )

        for widget in (header, self.header, self.hint, self.status_dot, self.chat):
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)

        self.root.update_idletasks()
        self._apply_window_style()
        self.show_original.trace_add("write", lambda *_: self._render())
        self.font_size.trace_add("write", lambda *_: self._render())
        self._render()
        self._poll()

    def _apply_window_style(self) -> None:
        inner = self.root.winfo_id()
        hwnd = ctypes.windll.user32.GetParent(inner) or inner
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def set_state(self, state: str) -> None:
        """idle / running / error 對應標題列的狀態燈顏色。"""
        colors = {"idle": theme.MUTED, "running": theme.OK, "error": theme.DANGER}
        self.status_dot.itemconfig(self._dot, fill=colors.get(state, theme.MUTED))

    def _start_drag(self, event) -> None:
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _on_drag(self, event) -> None:
        self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def clear(self) -> None:
        self.history.clear()
        self._render()

    def _render(self) -> None:
        size = self.font_size.get()
        self.chat.tag_configure("original", font=(theme.UI_FONT, max(10, size - 13)))
        self.chat.tag_configure("chinese", font=(theme.CJK_FONT, size, "bold"))
        self.chat.config(state="normal")
        self.chat.delete("1.0", "end")

        if not self.history:
            self.chat.insert("end", "等待影片聲音…", "waiting")
        else:
            for original, chinese in self.history:
                if self.show_original.get() and original:
                    self.chat.insert("end", f"{original}\n", "original")
                self.chat.insert("end", f" {chinese or original} \n", "chinese")

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
