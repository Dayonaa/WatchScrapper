from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SellerInfo(BaseModel):
    id: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None

class WatchListing(BaseModel):
    listing_id: str
    title: str
    price_raw: str
    price_sgd: Optional[float] = None
    condition: Optional[str] = "Unknown"
    description: Optional[str] = ""
    url: str
    thumbnail_url: Optional[str] = None
    photo_urls: List[str] = Field(default_factory=list)
    time_created: Optional[datetime] = None
    time_created_epoch: Optional[int] = None
    likes_count: Optional[int] = 0
    seller: Optional[SellerInfo] = None
    brand_keyword: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
