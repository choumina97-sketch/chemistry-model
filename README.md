# Chemistry Teaching Flashcards

這是一個本機可執行的化學分子教學圖卡網站。使用者可以輸入分子英文名稱，例如 `glucose`、`ethanol`、`aspirin`、`DDT`，網站會查詢分子資料、用 RDKit 建立分子、計算常見分子性質，並用 3Dmol.js 顯示互動式 3D 模型。

## 專案結構

```text
chemistry model/
├─ main.py
├─ chemistry_service.py
├─ requirements.txt
├─ README.md
├─ chemistry5.py
├─ legacy/
│  └─ chemistry5.py
├─ templates/
│  └─ index.html
└─ static/
   └─ style.css
```

`legacy/chemistry5.py` 是原始單檔程式備份。根目錄的 `chemistry5.py` 也保留未刪除。

## 安裝

建議先建立虛擬環境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安裝依賴：

```powershell
pip install -r requirements.txt
```

如果你的平台無法用 pip 安裝 RDKit，可以改用 conda 安裝 RDKit 後，再安裝其餘套件。

## 啟動

```powershell
uvicorn main:app --reload
```

啟動後在瀏覽器開啟：

```text
http://127.0.0.1:8000
```

## 測試分子

可以在搜尋欄輸入：

- `glucose`
- `ethanol`
- `aspirin`
- `DDT`
- `vitamin c`

網站會優先使用 PubChem CID/property 查詢，若失敗會依序嘗試 NCI/Cactus 與 OPSIN。

## 部署到 Render

此專案已加入 `render.yaml`，可部署為 Render Web Service。

Render 設定：

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

部署方式：

1. 將專案推送到 GitHub。
2. 到 Render 建立 New Web Service。
3. 連接該 GitHub repository。
4. Render 會讀取 `render.yaml` 並自動部署。

部署完成後，Render 會提供公開網址，任何有連結的人都可以使用。
