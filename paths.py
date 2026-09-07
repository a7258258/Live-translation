"""找出程式所在資料夾：開發時是原始碼目錄，打包成 exe 後是 exe 旁邊。"""

from __future__ import annotations

import sys
from pathlib import Path


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent
