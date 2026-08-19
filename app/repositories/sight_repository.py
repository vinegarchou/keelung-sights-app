from typing import List, Dict, Any
from app.database import get_database


class SightRepository:
    """Repository 專責與 MongoDB 溝通，處理景點資料之查詢、寫入與 upsert"""

    def __init__(self):
        self.db = get_database()
        self.collection = self.db["sights"]

    def get_by_zone(self, zone: str) -> List[Dict[str, Any]]:
        """從 MongoDB 中查詢指定行政區的所有景點 (排除 _id)"""
        cursor = self.collection.find({"zone": zone}, {"_id": 0})
        return list(cursor)

    def upsert_sight(self, sight_data: Dict[str, Any]) -> bool:
        """
        根據 sight_name 作為鍵進行 upsert
        若存在則更新，若不存在則插入
        """
        result = self.collection.update_one(
            {"sight_name": sight_data["sight_name"]},
            {"$set": sight_data},
            upsert=True
        )
        return result.upserted_id is not None or result.modified_count > 0

    def bulk_upsert(self, sights_list: List[Dict[str, Any]]) -> int:
        """批次更新/插入景點資料"""
        count = 0
        for sight_data in sights_list:
            self.upsert_sight(sight_data)
            count += 1
        return count
