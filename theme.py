"""深色主題的配色與 ttk 外觀設定，讓聊天視窗與控制項風格一致。"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

BG = "#12141A"          # 聊天區底色
PANEL = "#181B23"       # 控制列底色
HEADER = "#1F2430"      # 標題列底色
BUBBLE = "#232836"      # 譯文訊息底色
BORDER = "#2C3240"      # 分隔線與外框
TEXT = "#F3F5F9"        # 主要文字
MUTED = "#9BA4B4"       # 原文與說明文字
ACCENT = "#4F8CFF"      # 開始按鈕
DANGER = "#E5534B"      # 停止按鈕與錯誤狀態
OK = "#48C78E"          # 執行中狀態

CJK_FONT = "Microsoft JhengHei UI"
UI_FONT = "Segoe UI"


def apply_theme(root: tk.Misc) -> None:
    """把 ttk 元件改成深色，避免預設淺色控制項跟黑底衝突。"""
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        "Dark.TLabel",
        background=PANEL,
        foreground=MUTED,
        font=(UI_FONT, 9),
    )
    style.configure(
        "Status.TLabel",
        background=PANEL,
        foreground=MUTED,
        font=(CJK_FONT, 9),
    )
    style.configure(
        "Dark.TCombobox",
        fieldbackground=BUBBLE,
        background=BUBBLE,
        foreground=TEXT,
        arrowcolor=MUTED,
        bordercolor=BORDER,
        lightcolor=BUBBLE,
        darkcolor=BUBBLE,
        borderwidth=0,
        padding=4,
    )
    style.map(
        "Dark.TCombobox",
        fieldbackground=[("readonly", BUBBLE)],
        foreground=[("readonly", TEXT)],
        arrowcolor=[("active", TEXT)],
    )
    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground="#FFFFFF",
        borderwidth=0,
        focusthickness=0,
        font=(CJK_FONT, 10, "bold"),
        padding=(12, 6),
    )
    style.map(
        "Accent.TButton",
        background=[("disabled", BORDER), ("active", "#6BA0FF")],
        foreground=[("disabled", MUTED)],
    )
    style.configure(
        "Ghost.TButton",
        background=BUBBLE,
        foreground=TEXT,
        borderwidth=0,
        focusthickness=0,
        font=(CJK_FONT, 10),
        padding=(12, 6),
    )
    style.map(
        "Ghost.TButton",
        background=[("disabled", PANEL), ("active", BORDER)],
        foreground=[("disabled", "#5C6473"), ("active", TEXT)],
    )
    style.configure(
        "Stop.TButton",
        background=BUBBLE,
        foreground=TEXT,
        borderwidth=0,
        focusthickness=0,
        font=(CJK_FONT, 10),
        padding=(12, 6),
    )
    style.map(
        "Stop.TButton",
        background=[("disabled", PANEL), ("active", DANGER)],
        foreground=[("disabled", "#5C6473"), ("active", "#FFFFFF")],
    )

    # 下拉選單是原生 Listbox，要另外指定顏色才不會是白底
    root.option_add("*TCombobox*Listbox.background", BUBBLE)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
