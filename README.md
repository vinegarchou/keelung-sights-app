# 基隆景點導覽與 Web API (Keelung Tourism Explorer)

> **國立臺灣海洋大學 (NTOU) Web 專案 / 景點導覽與網頁爬蟲 API 系統**  
> 基於 **Python FastAPI + MongoDB Atlas + Repository & Service 雙層架構 + BeautifulSoup 爬蟲** 的基隆景點導覽平台。

---

## 雲端公開部署資訊 (Render)

* **雲端前端網頁與 Web API 網址**：`https://keelung-sights-app-owmc.onrender.com`
* **FastAPI 自動產生 Swagger 文件網址**：`https://keelung-sights-app-owmc.onrender.com/docs`
* **GitHub 專案儲存庫**：`https://github.com/vinegarchou/keelung-sights-app`

---

## 專案架構與檔案結構 (Project Structure)

```text
海大基隆網站/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 控制器、CORS、/docs 與 Lifespan 管理
│   ├── models.py                   # Pydantic 資料模型與範例規格
│   ├── crawler.py                  # TravelKing 景點 Web 爬蟲邏輯
│   ├── database.py                 # MongoDB Atlas (PyMongo + certifi) 連線檔
│   ├── seed_data.py                # 景點資料初始化 CLI 腳本 (python -m app.seed_data)
│   ├── repositories/
│   │   └── sight_repository.py     # Repository 模式：MongoDB CRUD & upsert 邏輯 (含 get_all)
│   └── services/
│       └── sight_service.py        # Service 模式：行政區正規化驗證與業務邏輯 (支援 ALL)
├── static/
│   ├── index.html                  
│   ├── main.js                     
│   ├── style.css                   
│   └── images/
│       ├── keelung_sunset_banner.jpg 
│       └── google_maps_icon.png     
├── requirements.txt                
├── Dockerfile                      
├── .dockerignore                   
├── .env.example                    # 環境變數範例檔
└── README.md                       # 專案說明文件
```

---

## 本機執行方式 (Local Setup)

### 1. 建立虛擬環境與安裝依賴
```bash
# 1. 建立並啟用虛擬環境
python3 -m venv venv
source venv/bin/activate

# 2. 安裝套件
pip install -r requirements.txt
```

### 2. 設定環境變數 (`.env`)
在專案根目錄建立 `.env` 檔案（請勿提交至 GitHub）：
```env
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.7ifoumf.mongodb.net/keelung_db?retryWrites=true&w=majority
DB_NAME=keelung_db
```

### 3. (可選) 執行景點資料初始化寫入 MongoDB
```bash
python -m app.seed_data
```

### 4. 啟動 FastAPI 服務
```bash
python -m uvicorn app.main:app --reload --port 8000
```
啟動後訪問：
* 前端網頁：[http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* API 互動式文件：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Docker 執行方式 (Docker Setup)

### 1. 建置 Docker Image
```bash
docker build -t keelung-sights-app .
```

### 2. 執行 Docker 容器
```bash
docker run -d   -p 8000:8000   -e MONGODB_URI="mongodb+srv://<user>:<password>@cluster0.7ifoumf.mongodb.net/keelung_db?retryWrites=true&w=majority"   -e DB_NAME="keelung_db"   --name keelung-app   keelung-sights-app
```
瀏覽器打開 [http://localhost:8000/](http://localhost:8000/) 檢視執行效果。

---

## 雲端環境變數設定 (Environment Variables)

在 Render 部署時，請在 **Environment** 頁面設定以下環境變數：

| 環境變數名稱 | 範例設定值 | 說明 |
| :--- | :--- | :--- |
| `MONGODB_URI` | `mongodb+srv://<user>:<password>@cluster0...` | MongoDB Atlas 雲端連線字串 |
| `DB_NAME` | `keelung_db` | 資料庫名稱 |
| `PORT` | `10000` *(由 Render 自動注入)* | 雲端動態指定之通訊埠 |

---

## Render 雲端部署步驟 (Render Deployment Steps)

1. **將專案推送到 GitHub 儲存庫**：
   ```bash
   git add .
   git commit -m "Update docs and deployment config"
   git push origin main
   ```

2. **登入 Render 並建立 Web Service**：
   * 登入 [Render Dashboard](https://dashboard.render.com/)。
   * 點擊 **New +** -> 選擇 **Web Service**。
   * 連結您的 GitHub 帳號並選擇 `keelung-sights-app` 專案。

3. **設定服務參數 (Service Settings)**：
   * **Name**: 填寫服務名稱 (例如 `keelung-sights-web`)。
   * **Language**: 選擇 **Docker**。
   * **Region**: 選擇鄰近區域 (如 Singapore)。
   * **Branch**: 選擇 **`main`**。
   * **Instance Type**: 選擇 **Free**。

4. **設定環境變數 (Environment Variables)**：
   * 在頁面下方點擊 **Environment Variables** -> **Add Environment Variable**：
     * `MONGODB_URI`: 填入您的 MongoDB Atlas 連線字串。
     * `DB_NAME`: 填入 `keelung_db`。

5. **部署與測試**：
   * 點擊 **Create Web Service**，Render 將會自動拉取最新代碼並執行 Docker 建置。
   * 建置完成後，訪問 Render 提供之公開網址（例如 `https://keelung-sights-web.onrender.com`）瀏覽首頁，並可在 `/docs` 測試 API。
