from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field


# ==========================================
# Pydantic Schemas (MongoDB & API)
# ==========================================
class Sight(BaseModel):
    sight_name: str = Field(..., example="泰安瀑布")
    zone: str = Field(..., example="七堵區")
    category: Optional[str] = Field("", example="風景區")
    photo_url: Optional[str] = Field("", example="https://photo.network.com.tw/scenery/example.jpg")
    description: Optional[str] = Field("", example="泰安瀑布位於七堵南方的草濫山區...")
    address: Optional[str] = Field("", example="基隆市七堵區泰安路")

    def __str__(self) -> str:
        return (
            f"SightName: {self.sight_name}\n"
            f"Zone: {self.zone}\n"
            f"Category: {self.category or ''}\n"
            f"PhotoURL: {self.photo_url or ''}\n"
            f"Description: {self.description or ''}\n"
            f"Address: {self.address or ''}\n"
        )


class SightBase(BaseModel):
    sight_name: str = Field(..., example="和平島地質公園")
    zone: str = Field(..., example="中正區")
    category: Optional[str] = Field("熱門景點", example="自然風景")
    photo_url: Optional[str] = Field(None, example="https://images.unsplash.com/photo-1542314831-068cd1dbfeeb")
    description: Optional[str] = Field(None, example="擁有千奇百怪的地質景觀與絕美海景觀景台。")
    address: Optional[str] = Field(None, example="基隆市中正區平一路360號")
    latitude: Optional[float] = Field(None, example=25.1601)
    longitude: Optional[float] = Field(None, example=121.7645)
    detail_url: Optional[str] = Field(None, example="https://www.neacoast-nsa.gov.tw")


class SightCreate(SightBase):
    pass


class SightResponse(SightBase):
    model_config = ConfigDict(from_attributes=True)


class SightListResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    sights: List[SightResponse]


class CrawlResponse(BaseModel):
    status: str
    message: str
    added_count: int
    updated_count: int
    total_sights: int


class DistrictStat(BaseModel):
    zone: str
    count: int


class StatsResponse(BaseModel):
    total_sights: int
    districts: List[DistrictStat]
    categories: Dict[str, int]
