import sys
import logging
from app.services.sight_service import SightService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """初始化資料 CLI 腳本：呼叫 SightService.refresh_sights() 將景點寫入 MongoDB Atlas"""
    logger.info("🚀 開始執行基隆景點資料初始化腳本 (寫入 MongoDB Atlas)...")
    try:
        service = SightService()
        count = service.refresh_sights()
        logger.info(f"✅ 資料初始化成功！共將 {count} 筆景點資料寫入/更新至 MongoDB。")
    except Exception as e:
        logger.error(f"❌ 初始化資料流程失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
