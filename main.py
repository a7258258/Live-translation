"""控制面板：開始擷取系統聲音 → 辨識 → 翻成繁中 → 投影字幕。"""

from __future__ import annotations

import multiprocessing
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from audio_capture import LoopbackCapture, list_speakers
from engine import TranslateEngine
from overlay import SubtitleOverlay


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Live-translation")
        self.root.geometry("420x320")
        self.root.resizable(False, False)

        self.audio_queue: queue.Queue = queue.Queue(maxsize=3)
        self.text_queue: queue.Queue = queue.Queue(maxsize=8)
        self.status_queue: queue.Queue = queue.Queue()
        self.capture: LoopbackCapture | None = None
        self.engine: TranslateEngine | None = None
        self.running = False

        self.model_size = tk.StringVar(value="base")
        self.language = tk.StringVar(value="auto")
        self.font_size = tk.IntVar(value=28)
        self.show_original = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="尚未開始")
        self.speaker_choice = tk.StringVar(value="")

        self._build_ui()
        self.overlay = SubtitleOverlay(
            self.root, self.text_queue, self.show_original, self.font_size
        )
        self._poll_status()

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 6}
        speakers = list_speakers()
        speaker_names = [name for _, name in speakers]
        if speaker_names:
            self.speaker_choice.set(speaker_names[0])

        ttk.Label(self.root, text="播放裝置（loopback）").pack(anchor="w", **pad)
        ttk.Combobox(
            self.root,
            textvariable=self.speaker_choice,
            values=speaker_names,
            state="readonly",
            width=48,
        ).pack(fill="x", padx=12)

        row = ttk.Frame(self.root)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Whisper 模型").pack(side="left")
        ttk.Combobox(
            row,
            textvariable=self.model_size,
            values=["tiny", "base", "small", "medium"],
            state="readonly",
            width=10,
        ).pack(side="left", padx=8)
        ttk.Label(row, text="來源語言").pack(side="left")
        ttk.Combobox(
            row,
            textvariable=self.language,
            values=["auto", "en", "ja", "ko", "zh", "es", "fr", "de"],
            state="readonly",
            width=8,
        ).pack(side="left", padx=8)

        ttk.Checkbutton(self.root, text="同時顯示原文", variable=self.show_original).pack(anchor="w", padx=12)
        size_row = ttk.Frame(self.root)
        size_row.pack(fill="x", padx=12)
        ttk.Label(size_row, text="字幕大小").pack(side="left")
        ttk.Scale(size_row, from_=18, to=48, variable=self.font_size, orient="horizontal").pack(
            side="left", fill="x", expand=True, padx=8
        )

        btns = ttk.Frame(self.root)
        btns.pack(fill="x", **pad)
        self.start_btn = ttk.Button(btns, text="開始翻譯", command=self.start)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.stop_btn = ttk.Button(btns, text="停止", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", expand=True, fill="x")

        ttk.Label(self.root, textvariable=self.status, wraplength=390).pack(anchor="w", **pad)

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
            return

        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self._worker, daemon=True).start()
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
        self.root.after(120, self._poll_status)


def main() -> None:
    root = tk.Tk()
    App(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
