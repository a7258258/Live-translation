# 即時中文字幕

把電腦**正在播放的影片／音樂聲音**轉成**繁體中文字幕**，疊在螢幕下方（可點穿，不擋滑鼠）。

流程：系統喇叭 loopback → Whisper 語音辨識 → Google 翻譯成繁中 → 置頂字幕層。

## 環境

- Windows 10 / 11
- Python 3.10 以上
- 需要能上網（翻譯走 Google；第一次還會下載 Whisper 模型）

```powershell
cd "C:\Users\Yubin\OneDrive\桌面\workshop\live-zh-subtitles"
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

## Git 怎麼連這個專案

這個資料夾已經 `git init`，目前**還沒有遠端（GitHub）**。你這台是原生 Windows，Cursor 的 Origin（`origin.cursor.com`）**還不能用**，請用 GitHub。

### 第一次把專案推到 GitHub

1. 到 [GitHub New repository](https://github.com/new) 建一個空 repo（不要勾 README）
2. 在專案目錄執行：

```powershell
cd "C:\Users\Yubin\OneDrive\桌面\workshop\live-zh-subtitles"
git add .
git commit -m "Add live Chinese subtitle overlay"
git remote add origin https://github.com/你的帳號/live-zh-subtitles.git
git push -u origin main
```

把 `你的帳號` 換成你的 GitHub 帳號。之後改完程式：

```powershell
git add .
git commit -m "說明這次改了什麼"
git push
```

### 如果是別人已經有的 GitHub repo

```powershell
git clone https://github.com/帳號/live-zh-subtitles.git
cd live-zh-subtitles
```

本機舊專案 `Translate`（`a7258258/Instant-Translation`）是終端機印翻譯、還要 VB-CABLE。這個專案改成直接聽系統喇叭，並把字幕投影到螢幕上。

## 注意

- 耳機聽影片時，請選「那顆耳機／喇叭」當播放裝置，否則 loopback 會是空的。
- 第一次載入 `base` 模型可能要幾分鐘。
- 翻譯品質取決於 Whisper 聽得清不清楚；雜音大、重疊對白會漏句。
