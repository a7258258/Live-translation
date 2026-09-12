# Live-translation

把電腦**正在播放的影片／音樂聲音**轉成**繁體中文字幕**，顯示在可拖曳的置頂聊天面板。每個新句會參考最近 5 組對話，先修正語音辨識結果，再翻成連貫的繁體中文。

流程：系統喇叭 loopback → Whisper 語音辨識 → 本機 Qwen 依上下文校正與翻譯 → 聊天字幕面板。

## 第一次使用：安裝本機 AI

1. 從 [Ollama 官方網站](https://ollama.com/download/windows) 安裝 Windows 版 Ollama。
2. 開啟 PowerShell，下載 Qwen3 8B 模型：

```powershell
ollama pull qwen3:8b
```

模型約數 GB，只需下載一次。使用程式前請保持 Ollama 在背景執行；翻譯內容只會送到本機 `127.0.0.1`，不會送到線上翻譯服務。

## 直接執行（exe）

雙擊 `dist/Live-translation/Live-translation.exe`。請整包 `dist/Live-translation` 一起帶走，不要只複製單一 exe。第一次按「開始翻譯」會把 Whisper 語音辨識模型下載到 exe 旁邊的 `whisper-models`。

## 用 Python 執行

- Windows 10 / 11
- Python 3.10 以上
- 第一次下載 Ollama 與 Whisper 模型時需要網路；完成後上下文翻譯在本機執行

```powershell
cd "C:\Users\Yubin\OneDrive\桌面\workshop\Live-translation"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

1. 在控制視窗選「你正在出聲的喇叭」
2. 模型建議先用 `base`；要更準再改 `small` / `medium`（會比較慢）
3. 來源語言不確定就用 `auto`
4. 按「開始翻譯」，再開影片（聲音走系統喇叭，不要只走耳機且選錯裝置）
5. 聊天面板保留最近 10 組原文與繁中；取消「同時顯示原文」可只看翻譯
6. 按住面板標題或內容即可拖曳；控制視窗可停止或調整字體
7. 按「停止」會清空聊天與上下文，下一部影片不會沿用前一部的內容

- 耳機聽影片時，請選「那顆耳機／喇叭」當播放裝置，否則 loopback 會是空的。
- 第一次載入 `base` 模型可能要幾分鐘。
- Qwen3 8B 適合本機上下文翻譯，但速度仍取決於顯示卡與同時執行的程式。
- 翻譯品質取決於 Whisper 聽得清不清楚；雜音大、重疊對白仍可能漏句。
