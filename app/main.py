import os
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.models import Sight
from app.services.sight_service import SightService
from app.database import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 Service 服務層實例
service = SightService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI App 啟動與關閉之 lifespan 連線生命週期管理"""
    logger.info("正在檢查並初始化 MongoDB Atlas 連線...")
    try:
        db = get_database()
        db.command("ping")
        logger.info("✅ 成功連線至 MongoDB Atlas 資料庫！")
    except Exception as e:
        logger.error(f"❌ MongoDB Atlas 連線異常: {e}")
    yield
    logger.info("關閉服務...")


app = FastAPI(
    title="Keelung Sights Web API (基隆景點 API)",
    description="透過 FastAPI 與 MongoDB Atlas 提供基隆各行政區景點檢索。",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str = "ok"


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """服務健康檢查 API"""
    return {"status": "ok"}


@app.get(
    "/sights",
    response_model=List[Sight],
    summary="從 MongoDB 取得特定行政區或全部景點資料",
    description="傳入行政區名稱 query parameter (zone)，例如 'ALL'、'七堵' 或 '七堵區'，回傳 MongoDB 中對應的景點 Sight 物件清單。",
    tags=["Sights"]
)
def get_sights_by_zone(
    zone: str = Query("ALL", description="行政區名稱 (例如：ALL, 七堵區, 中正區)")
):
    """
    HTTP Controller / Router：
    只負責讀取 query parameter、呼叫 Service 層處理業務邏輯、並回傳 JSON。
    """
    try:
        return service.get_sights_by_zone(zone)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"取得景點資料失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="伺服器內部錯誤"
        )


# 掛載靜態頁面
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({
        "message": "Keelung Sights API (MongoDB Atlas Version) is running",
        "docs": "/docs",
        "example": "/sights?zone=ALL"
    })
