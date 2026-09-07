"""翻成繁體中文：Google 行動版 → Google gtx API → MyMemory，前一個失敗就換下一個。"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request

TIMEOUT = 10
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
# Google 擋人時會回一張錯誤頁，內文長得像「Error 500 (Server Error)!!1」，不能當譯文用
ERROR_PAGE = re.compile(r"^Error \d+ \(", re.IGNORECASE)


def _fetch(url: str) -> str:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8", "replace")


def _google_mobile(text: str, source: str) -> str:
    raw = _fetch(
        "https://translate.google.com/m?sl=%s&tl=zh-TW&q=%s"
        % (source, urllib.parse.quote(text))
    )
    found = re.search(r'class="result-container">(.*?)</div>', raw, re.S)
    if not found:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", found.group(1))).strip()


def _google_api(text: str, source: str) -> str:
    raw = _fetch(
        "https://translate.googleapis.com/translate_a/single"
        "?client=gtx&sl=%s&tl=zh-TW&dt=t&q=%s" % (source, urllib.parse.quote(text))
    )
    parts = json.loads(raw)[0]
    return "".join(part[0] for part in parts if part[0]).strip()


def _mymemory(text: str, source: str) -> str:
    pair = "%s|zh-TW" % ("en" if source == "auto" else source)
    raw = _fetch(
        "https://api.mymemory.translated.net/get?langpair=%s&q=%s"
        % (urllib.parse.quote(pair), urllib.parse.quote(text))
    )
    return json.loads(raw)["responseData"]["translatedText"].strip()


class Translator:
    """_order 會把上次成功的來源排到最前面，避免每句都重試已經壞掉的那個。"""

    def __init__(self):
        self._order = [_google_mobile, _google_api, _mymemory]

    def to_chinese(self, text: str, source: str = "auto") -> str:
        if not text.strip():
            return ""
        for index, backend in enumerate(self._order):
            try:
                result = backend(text, source)
            except Exception:
                continue
            if result and not ERROR_PAGE.match(result):
                if index:
                    self._order.insert(0, self._order.pop(index))
                return result
        return ""
