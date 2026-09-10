import re
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import WatchListing, SellerInfo

def clean_price(price_str: Optional[str]) -> Optional[float]:
    """Convert price string like 'S$37,990' or '$14,350' to float."""
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", price_str)
    try:
        return float(cleaned)
    except ValueError:
        return None

def parse_listing_card(card: Dict[str, Any], brand_keyword: Optional[str] = None) -> Optional[WatchListing]:
    """Parse a single listing card from Carousell's SearchListing JSON data."""
    listing_id = str(card.get("id") or card.get("listingID") or "")
    if not listing_id:
        return None

    title = card.get("title") or ""
    price_raw = card.get("price") or ""
    description = card.get("description") or ""
    likes_count = card.get("likesCount", 0)
    thumbnail_url = card.get("thumbnailURL") or ""

    # Extract all photo URLs
    photo_urls = []
    if "media" in card and isinstance(card["media"], list):
        for m in card["media"]:
            if isinstance(m, dict):
                photo_item = m.get("photoItem", {})
                url = photo_item.get("progressiveUrl") or photo_item.get("url")
                if url:
                    photo_urls.append(url)
    if not photo_urls and thumbnail_url:
        photo_urls.append(thumbnail_url)

    # Extract creation timestamp from aboveFold
    time_created_epoch = None
    time_created = None
    if "aboveFold" in card and isinstance(card["aboveFold"], list):
        for af in card["aboveFold"]:
            if isinstance(af, dict) and af.get("component") == "time_created":
                ts = af.get("timestampContent", {}).get("seconds", {})
                if isinstance(ts, dict):
                    time_created_epoch = ts.get("low")
                elif isinstance(ts, (int, float)):
                    time_created_epoch = int(ts)
                if time_created_epoch:
                    try:
                        time_created = datetime.utcfromtimestamp(time_created_epoch)
                    except Exception:
                        pass
                break

    # Extract condition or extra info from belowFold
    condition = "Unknown"
    if "belowFold" in card and isinstance(card["belowFold"], list):
        for bf in card["belowFold"]:
            if isinstance(bf, dict) and bf.get("component") == "paragraph":
                text = bf.get("stringContent", "").strip()
                if text.lower() in [
                    "brand new", "like new", "lightly used", "well used", "heavily used",
                    "new", "pre-owned", "used", "mint", "brand new in box"
                ]:
                    condition = text
                    break

    # Extract seller info
    seller_data = card.get("seller") or {}
    seller = None
    if seller_data:
        uname = seller_data.get("username")
        seller = SellerInfo(
            id=str(seller_data.get("id") or ""),
            username=uname,
            first_name=seller_data.get("firstName"),
            profile_url=f"https://www.carousell.sg/u/{uname}/" if uname else None,
            avatar_url=seller_data.get("profilePicture")
        )

    # Build direct product URL
    url = f"https://www.carousell.sg/p/{listing_id}"

    return WatchListing(
        listing_id=listing_id,
        title=title,
        price_raw=price_raw,
        price_sgd=clean_price(price_raw),
        condition=condition,
        description=description,
        url=url,
        thumbnail_url=thumbnail_url,
        photo_urls=photo_urls,
        time_created=time_created,
        time_created_epoch=time_created_epoch,
        likes_count=likes_count,
        seller=seller,
        brand_keyword=brand_keyword
    )

def extract_listings_from_html(html_content: str, brand_keyword: Optional[str] = None) -> List[WatchListing]:
    """Extract watch listings from Carousell page HTML using embedded JSON states."""
    listings: List[WatchListing] = []
    seen_ids = set()

    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html_content, re.DOTALL)
    for s in scripts:
        s = s.strip()
        if s.startswith('{"Application"') or '"SearchListing"' in s:
            try:
                data = json.loads(s)
                search_listing = data.get("SearchListing", {})
                cards = search_listing.get("listingCards", [])
                for c in cards:
                    parsed = parse_listing_card(c, brand_keyword=brand_keyword)
                    if parsed and parsed.listing_id not in seen_ids:
                        seen_ids.add(parsed.listing_id)
                        listings.append(parsed)
            except Exception:
                continue

    # Fallback to Schema.org ItemList if SearchListing wasn't found
    if not listings:
        for s in scripts:
            s = s.strip()
            if s.startswith('{"@context"') and "ItemList" in s:
                try:
                    data = json.loads(s)
                    items = data.get("itemListElement", [])
                    for it in items:
                        prod = it.get("item", {})
                        p_url = prod.get("url") or ""
                        # Extract listing id from url
                        lid_match = re.search(r"-(\d+)/?$", p_url) or re.search(r"/p/(\d+)", p_url)
                        lid = lid_match.group(1) if lid_match else p_url
                        if lid and lid not in seen_ids:
                            seen_ids.add(lid)
                            offers = prod.get("offers", {})
                            price_val = str(offers.get("price", ""))
                            price_curr = offers.get("priceCurrency", "SGD")
                            price_str = f"{price_curr} {price_val}" if price_val else ""
                            listings.append(
                                WatchListing(
                                    listing_id=lid,
                                    title=prod.get("name") or "",
                                    price_raw=price_str,
                                    price_sgd=clean_price(price_val),
                                    description=prod.get("description") or "",
                                    url=p_url or f"https://www.carousell.sg/p/{lid}",
                                    thumbnail_url=prod.get("image"),
                                    photo_urls=[prod.get("image")] if prod.get("image") else [],
                                    brand_keyword=brand_keyword
                                )
                            )
                except Exception:
                    continue

    return listings
