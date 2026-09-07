"""語音辨識（Whisper）+ 翻成繁體中文。"""

from __future__ import annotations

from faster_whisper import WhisperModel

from paths import app_dir
from translator import Translator


class TranslateEngine:
    """
    model_size: tiny / base / small / medium。越大越準、越慢。
    source_language: None 代表自動偵測；也可指定 en、ja、ko 等。
    """

    def __init__(self, model_size: str = "base", source_language: str | None = None):
        self.source_language = source_language or None
        model_dir = app_dir() / "whisper-models"
        model_dir.mkdir(parents=True, exist_ok=True)
        self._model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            download_root=str(model_dir),
        )
        self._translator = Translator()

    def transcribe_and_translate(self, audio_16k) -> tuple[str, str]:
        segments, info = self._model.transcribe(
            audio_16k,
            language=self.source_language,
            vad_filter=True,
            without_timestamps=True,
        )
        original = "".join(seg.text for seg in segments).strip()
        if not original:
            return "", ""
        source = self.source_language or info.language or "auto"
        chinese = self._translator.to_chinese(original, source)
        return original, chinese
