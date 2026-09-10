import json
import os
from typing import List
import pandas as pd
from .models import WatchListing

def listings_to_dataframe(listings: List[WatchListing]) -> pd.DataFrame:
    """Convert list of WatchListing models to pandas DataFrame."""
    rows = []
    for l in listings:
        rows.append({
            "listing_id": l.listing_id,
            "title": l.title,
            "brand": l.brand_keyword,
            "price_raw": l.price_raw,
            "price_sgd": l.price_sgd,
            "condition": l.condition,
            "likes_count": l.likes_count,
            "time_created": l.time_created.strftime("%Y-%m-%d %H:%M:%S") if l.time_created else None,
            "seller_username": l.seller.username if l.seller else None,
            "seller_name": l.seller.first_name if l.seller else None,
            "seller_url": l.seller.profile_url if l.seller else None,
            "url": l.url,
            "thumbnail_url": l.thumbnail_url,
            "photo_urls": ", ".join(l.photo_urls),
            "description": l.description,
            "scraped_at": l.scraped_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return pd.DataFrame(rows)

def export_to_csv(listings: List[WatchListing], filepath: str) -> str:
    """Export watch listings to CSV format."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    df = listings_to_dataframe(listings)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return filepath

def export_to_excel(listings: List[WatchListing], filepath: str) -> str:
    """Export watch listings to Excel format (.xlsx)."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    df = listings_to_dataframe(listings)
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Watches", index=False)
    return filepath

def export_to_json(listings: List[WatchListing], filepath: str) -> str:
    """Export watch listings to JSON format."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    data = [l.model_dump(mode="json") for l in listings]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filepath
