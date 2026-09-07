"""從目前正在播的喇叭做 WASAPI loopback，等於錄「系統正在出的聲音」。"""

from __future__ import annotations

import queue
import threading

import numpy as np
import soundcard as sc

CAPTURE_RATE = 16000
CHUNK_SECONDS = 4.0
SILENCE_RMS = 0.008


class LoopbackCapture:
    """
    speaker_id: 要用哪顆喇叭的 loopback。None 代表系統預設喇叭。
    chunk_queue: 辨識執行緒會從這裡拿走 float32 mono 音訊。
    """

    def __init__(self, chunk_queue: queue.Queue, speaker_id: str | None = None):
        self.chunk_queue = chunk_queue
        self.speaker_id = speaker_id
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        speaker = (
            sc.get_speaker(self.speaker_id)
            if self.speaker_id
            else sc.default_speaker()
        )
        mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(mic,),
            daemon=True,
        )
        self._thread.start()
        return speaker.name

    def stop(self) -> None:
        self._stop.set()

    def _run(self, mic) -> None:
        frames = int(CAPTURE_RATE * CHUNK_SECONDS)
        with mic.recorder(samplerate=CAPTURE_RATE, channels=1) as rec:
            while not self._stop.is_set():
                data = rec.record(numframes=frames)
                mono = np.asarray(data, dtype=np.float32).reshape(-1)
                rms = float(np.sqrt(np.mean(mono**2))) if mono.size else 0.0
                if rms < SILENCE_RMS:
                    continue
                try:
                    self.chunk_queue.put_nowait(mono)
                except queue.Full:
                    pass


def list_speakers() -> list[tuple[str, str]]:
    """回傳 (id, name)，給控制面板選裝置用。"""
    return [(sp.id, sp.name) for sp in sc.all_speakers()]
