"""用本機 Ollama 依照前文修正語音辨識文字，再翻成繁體中文。"""

from __future__ import annotations

import json
import os
import shutil
import urllib.request
import urllib.error
from collections import deque
from pathlib import Path

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen3:8b"
REQUEST_TIMEOUT = 120
DISPLAY_HISTORY_LIMIT = 10
CONTEXT_HISTORY_LIMIT = 5

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "corrected_source": {"type": "string"},
        "zh_tw": {"type": "string"},
    },
    "required": ["corrected_source", "zh_tw"],
}

SYSTEM_PROMPT = """你是即時影片字幕校正與翻譯器。
根據提供的最近對話上下文，只處理「最新辨識文字」：
1. 修正語音辨識造成的同音字、斷句、專有名詞與代名詞錯誤。
2. 不可改變原意，不可加入原文沒有的資訊。
3. 翻譯為自然、連貫的繁體中文。
4. 只輸出符合指定 schema 的 JSON，不要解釋。"""


class OllamaError(RuntimeError):
    """Ollama 無法提供上下文翻譯。"""


class OllamaNotInstalledError(OllamaError):
    pass


class OllamaNotRunningError(OllamaError):
    pass


class OllamaModelMissingError(OllamaError):
    pass


def _ollama_executable_exists() -> bool:
    if shutil.which("ollama"):
        return True
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return False
    return (Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe").exists()


def _request(path: str, payload: dict | None = None, timeout: int = 10) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise OllamaError(f"Ollama 回傳 HTTP {exc.code}，請稍後再試。") from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        if _ollama_executable_exists():
            raise OllamaNotRunningError(
                "Ollama 已安裝但服務沒有啟動，請先開啟 Ollama。"
            ) from exc
        raise OllamaNotInstalledError(
            "尚未安裝 Ollama，請先到 https://ollama.com/download 安裝。"
        ) from exc


def check_ollama_ready() -> None:
    tags = _request("/api/tags")
    names = {model.get("name", "") for model in tags.get("models", [])}
    if MODEL not in names and f"{MODEL}-latest" not in names:
        raise OllamaModelMissingError(
            f"找不到本機模型 {MODEL}，請在 PowerShell 執行：ollama pull {MODEL}"
        )


class Translator:
    """history 保存最近 10 組字幕，其中最近 5 組會提供給模型判斷新句。"""

    def __init__(self):
        self.history: deque[tuple[str, str]] = deque(maxlen=DISPLAY_HISTORY_LIMIT)

    def reset(self) -> None:
        self.history.clear()

    def correct_and_translate(self, text: str, source: str = "auto") -> tuple[str, str]:
        if not text.strip():
            return "", ""

        context = [
            {"source": original, "zh_tw": chinese}
            for original, chinese in list(self.history)[-CONTEXT_HISTORY_LIMIT:]
        ]
        user_content = json.dumps(
            {
                "source_language": source,
                "recent_context": context,
                "latest_recognition": text.strip(),
            },
            ensure_ascii=False,
        )
        response = _request(
            "/api/chat",
            {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                "stream": False,
                "think": False,
                "format": RESULT_SCHEMA,
                "options": {"temperature": 0},
                "keep_alive": "10m",
            },
            timeout=REQUEST_TIMEOUT,
        )

        try:
            result = json.loads(response["message"]["content"])
            corrected = result["corrected_source"].strip()
            chinese = result["zh_tw"].strip()
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise OllamaError("本機 AI 回傳格式不正確，請稍後再試。") from exc

        if not corrected or not chinese:
            raise OllamaError("本機 AI 沒有產生完整字幕，請稍後再試。")

        self.history.append((corrected, chinese))
        return corrected, chinese
