from typing import List, Optional
from app.models import Sight
from app.repositories.sight_repository import SightRepository
from app.crawler import KeelungSightsCrawler

# 基隆市 7 大有效行政區集合與簡寫對照
VALID_ZONES = {"中山區", "信義區", "仁愛區", "中正區", "安樂區", "七堵區", "暖暖區"}
ZONE_ALIAS = {
    "中山": "中山區", "信義": "信義區", "仁愛": "仁愛區",
    "中正": "中正區", "安樂": "安樂區", "七堵": "七堵區", "暖暖": "暖暖區"
}


class SightService:
    """Service 業務邏輯層：連結 API 與 Repository，處理行政區驗證與資料協調"""

    def __init__(self, repository: Optional[SightRepository] = None, crawler: Optional[KeelungSightsCrawler] = None):
        self.repository = repository or SightRepository()
        self.crawler = crawler or KeelungSightsCrawler()

    def normalize_zone(self, zone: str) -> str:
        """
        將 '七堵'、'七堵區' 等輸入統一轉為完整行政區名稱，
        並檢查是否為基隆市有效行政區。若無效則拋出 ValueError。
        """
        if not zone or not zone.strip():
            return "ALL"
        
        clean_z = zone.strip()
        if clean_z.upper() in ["ALL", "全部", "全部景點"]:
            return "ALL"

        normalized = ZONE_ALIAS.get(clean_z, clean_z if clean_z.endswith("區") else f"{clean_z}區")

        if normalized not in VALID_ZONES:
            raise ValueError(f"無效的基隆行政區名稱: '{zone}'。有效區域為: ALL, {', '.join(sorted(VALID_ZONES))}")
        
        return normalized

    def get_sights_by_zone(self, zone: str) -> List[Sight]:
        """
        接收 API 傳入的區域名稱，完成正規化與驗證後，
        呼叫 Repository 從 MongoDB 取得景點資料並回傳 List[Sight]。
        支援 zone='ALL' 取得全部景點。
        """
        normalized_zone = self.normalize_zone(zone)

        if normalized_zone == "ALL":
            raw_sights = self.repository.get_all()
            if not raw_sights:
                self.refresh_sights()
                raw_sights = self.repository.get_all()
            return [Sight(**item) for item in raw_sights]

        raw_sights = self.repository.get_by_zone(normalized_zone)
        
        # 若資料庫中無資料，自動呼叫爬蟲補充並寫入 MongoDB
        if not raw_sights:
            crawled = self.crawler.get_items(normalized_zone)
            for sight in crawled:
                sight_dict = sight.model_dump() if hasattr(sight, 'model_dump') else sight.dict()
                self.repository.upsert_sight(sight_dict)
            raw_sights = self.repository.get_by_zone(normalized_zone)

        return [Sight(**item) for item in raw_sights]

    def refresh_sights(self) -> int:
        """
        呼叫爬蟲取得基隆各區景點資料，並透過 Repository 將資料 upsert 到 MongoDB。
        回傳成功寫入/更新的景點總數。
        """
        total_count = 0
        for zone in VALID_ZONES:
            crawled_sights = self.crawler.get_items(zone)
            for sight in crawled_sights:
                sight_dict = sight.model_dump() if hasattr(sight, 'model_dump') else sight.dict()
                self.repository.upsert_sight(sight_dict)
                total_count += 1
        return total_count
