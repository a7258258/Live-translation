# Live-translation

把電腦**正在播放的影片／音樂聲音**轉成**繁體中文字幕**，疊在螢幕下方。

流程：系統喇叭 loopback → Whisper 語音辨識 → Google 翻譯成繁中 → 置頂字幕層。

## 直接執行（exe）

雙擊 `dist/Live-translation/Live-translation.exe`。請整包 `dist/Live-translation` 一起帶走，不要只複製單一 exe。第一次按「開始翻譯」會把 Whisper 模型下載到 exe 旁邊的 `whisper-models`。

## 用 Python 執行

- Windows 10 / 11
- Python 3.10 以上
- 需要能上網（翻譯走 Google；第一次還會下載 Whisper 模型）

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
5. 字幕出現在螢幕底部；控制視窗可停止或調字體
6. 字幕有黑色底色，直接用滑鼠拖曳就能換位置

- 耳機聽影片時，請選「那顆耳機／喇叭」當播放裝置，否則 loopback 會是空的。
- 第一次載入 `base` 模型可能要幾分鐘。
- 翻譯品質取決於 Whisper 聽得清不清楚；雜音大、重疊對白會漏句。
