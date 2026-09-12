"""單一聊天視窗：開始擷取系統聲音 → 辨識 → 依上下文翻成繁中。"""

from __future__ import annotations

import multiprocessing
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import theme
from audio_capture import LoopbackCapture, list_speakers
from engine import TranslateEngine
from overlay import SubtitleOverlay


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Live-translation")
        theme.apply_theme(self.root)

        self.audio_queue: queue.Queue = queue.Queue(maxsize=3)
        self.text_queue: queue.Queue = queue.Queue(maxsize=8)
        self.status_queue: queue.Queue = queue.Queue()
        self.capture: LoopbackCapture | None = None
        self.engine: TranslateEngine | None = None
        self.running = False

        self.model_size = tk.StringVar(value="base")
        self.language = tk.StringVar(value="auto")
        self.font_size = tk.IntVar(value=28)
        self.font_label = tk.StringVar(value="28")
        self.font_size.trace_add("write", lambda *_: self.font_label.set(str(self.font_size.get())))
        self.show_original = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="尚未開始")
        self.speaker_choice = tk.StringVar(value="")

        self.overlay = SubtitleOverlay(
            self.root, self.text_queue, self.show_original, self.font_size
        )
        self._build_controls(self.overlay.controls)
        self._poll_status()

    def _build_controls(self, parent: tk.Frame) -> None:
        speakers = list_speakers()
        speaker_names = [name for _, name in speakers]
        if speaker_names:
            self.speaker_choice.set(speaker_names[0])

        top = tk.Frame(parent, bg=theme.PANEL)
        top.pack(fill="x", padx=16, pady=(12, 6))
        ttk.Label(top, text="播放裝置", style="Dark.TLabel").pack(side="left")
        ttk.Combobox(
            top,
            textvariable=self.speaker_choice,
            values=speaker_names,
            state="readonly",
            style="Dark.TCombobox",
        ).pack(side="left", fill="x", expand=True, padx=(10, 0))

        row = tk.Frame(parent, bg=theme.PANEL)
        row.pack(fill="x", padx=16, pady=6)
        ttk.Label(row, text="Whisper", style="Dark.TLabel").pack(side="left")
        ttk.Combobox(
            row,
            textvariable=self.model_size,
            values=["tiny", "base", "small", "medium"],
            state="readonly",
            width=9,
            style="Dark.TCombobox",
        ).pack(side="left", padx=(10, 18))
        ttk.Label(row, text="語言", style="Dark.TLabel").pack(side="left")
        ttk.Combobox(
            row,
            textvariable=self.language,
            values=["auto", "en", "ja", "ko", "zh", "es", "fr", "de"],
            state="readonly",
            width=7,
            style="Dark.TCombobox",
        ).pack(side="left", padx=(10, 18))
        ttk.Label(row, text="字體", style="Dark.TLabel").pack(side="left")
        ttk.Button(
            row, text="A －", width=4, style="Ghost.TButton",
            command=lambda: self._adjust_font(-2),
        ).pack(side="left", padx=(10, 4))
        ttk.Label(row, textvariable=self.font_label, style="Dark.TLabel", width=3).pack(side="left")
        ttk.Button(
            row, text="A ＋", width=4, style="Ghost.TButton",
            command=lambda: self._adjust_font(2),
        ).pack(side="left", padx=(4, 18))
        tk.Checkbutton(
            row,
            text="同時顯示原文",
            variable=self.show_original,
            bg=theme.PANEL,
            fg=theme.MUTED,
            activebackground=theme.PANEL,
            activeforeground=theme.TEXT,
            selectcolor=theme.BUBBLE,
            highlightthickness=0,
            borderwidth=0,
            font=(theme.CJK_FONT, 9),
            cursor="hand2",
        ).pack(side="left")

        actions = tk.Frame(parent, bg=theme.PANEL)
        actions.pack(fill="x", padx=16, pady=(2, 12))
        ttk.Label(
            actions,
            textvariable=self.status,
            style="Status.TLabel",
            wraplength=620,
        ).pack(side="left", fill="x", expand=True)
        self.stop_btn = ttk.Button(
            actions, text="停止", command=self.stop, state="disabled", style="Stop.TButton"
        )
        self.stop_btn.pack(side="right", padx=(8, 0))
        self.start_btn = ttk.Button(
            actions, text="開始翻譯", command=self.start, style="Accent.TButton"
        )
        self.start_btn.pack(side="right")

    def _adjust_font(self, delta: int) -> None:
        self.font_size.set(min(48, max(18, self.font_size.get() + delta)))

    def start(self) -> None:
        if self.running:
            return
        self.overlay.clear()
        self._clear_queue(self.audio_queue)
        self._clear_queue(self.text_queue)
        lang = self.language.get()
        source = None if lang == "auto" else lang
        self.status.set("正在檢查 Ollama 並載入 Whisper 模型，請稍候…")
        self.root.update_idletasks()
        try:
            self.engine = TranslateEngine(self.model_size.get(), source)
            speaker_name = self.speaker_choice.get() or None
            self.capture = LoopbackCapture(self.audio_queue, speaker_name)
            used = self.capture.start()
        except Exception as exc:
            messagebox.showerror("無法開始", str(exc))
            self.status.set(f"失敗：{exc}")
            self.overlay.set_state("error")
            return

        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self._worker, daemon=True).start()
        self.overlay.set_state("running")
        self.status.set(f"正在聽「{used}」的系統聲音")

    def stop(self) -> None:
        self.running = False
        if self.capture:
            self.capture.stop()
        if self.engine:
            self.engine.reset_context()
        self.overlay.clear()
        self._clear_queue(self.audio_queue)
        self._clear_queue(self.text_queue)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.overlay.set_state("idle")
        self.status.set("已停止")

    def _worker(self) -> None:
        while self.running:
            try:
                chunk = self.audio_queue.get(timeout=0.4)
            except queue.Empty:
                continue
            if not self.engine:
                continue
            try:
                self.status_queue.put("正在辨識並依照上下文修正翻譯…")
                original, chinese = self.engine.transcribe_and_translate(chunk)
            except Exception as exc:
                self.status_queue.put(f"翻譯錯誤：{exc}")
                continue
            if original or chinese:
                try:
                    self.text_queue.put_nowait((original, chinese))
                except queue.Full:
                    pass
                self.status_queue.put("字幕已新增，正在等待下一句…")

    @staticmethod
    def _clear_queue(target: queue.Queue) -> None:
        while True:
            try:
                target.get_nowait()
            except queue.Empty:
                break

    def _poll_status(self) -> None:
        latest = None
        while True:
            try:
                latest = self.status_queue.get_nowait()
            except queue.Empty:
                break
        if latest is not None:
            self.status.set(latest)
            if self.running:
                self.overlay.set_state("error" if latest.startswith("翻譯錯誤") else "running")
        self.root.after(120, self._poll_status)


def main() -> None:
    root = tk.Tk()
    App(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
