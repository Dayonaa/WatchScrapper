import re
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from .models import WatchListing, SellerInfo
from .parser import clean_price

CHRONO24_BASE_URL = "https://www.chrono24.sg"

class Chrono24Scraper:
    def __init__(self, user_agent: Optional[str] = None):
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )

    def _build_search_url(
        self,
        query: str,
        sort: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        page: int = 1
    ) -> str:
        params = {
            "query": query,
            "dosearch": "true",
            "searchexplain": "1"
        }
        if page > 1:
            params["showpage"] = str(page)

        # Sort mapping for Chrono24
        # 1: Price asc, 2: Price desc, 6: Date desc (newest)
        if sort in ["price_asc", "price"]:
            params["sortorder"] = "1"
        elif sort in ["price_desc"]:
            params["sortorder"] = "2"
        elif sort in ["recent", "newest"]:
            params["sortorder"] = "6"

        if min_price is not None:
            params["priceFrom"] = str(int(min_price))
        if max_price is not None:
            params["priceTo"] = str(int(max_price))

        return f"{CHRONO24_BASE_URL}/search/index.htm?{urllib.parse.urlencode(params)}"

    def parse_card_html(self, card_el, brand_keyword: Optional[str] = None) -> Optional[WatchListing]:
        """Parse individual Chrono24 watch card element."""
        link_el = card_el.find("a", href=lambda h: h and ("--id" in h or "-id" in h))
        if not link_el:
            return None

        href = link_el.get("href", "")
        if not href.startswith("http"):
            full_url = f"{CHRONO24_BASE_URL}{href}"
        else:
            full_url = href

        # Extract listing ID
        id_match = re.search(r"id(\d+)\.htm", href)
        listing_id = id_match.group(1) if id_match else href

        # Extract images
        img_el = card_el.find("img")
        thumbnail_url = None
        if img_el:
            thumbnail_url = img_el.get("src") or img_el.get("data-src")

        # Extract lines of text
        lines = [t.strip() for t in card_el.get_text(separator="\n").split("\n") if t.strip()]
        # Filter out UI controls like 'Go to slide X', 'Popular', etc.
        meaningful_lines = [
            l for l in lines 
            if not l.startswith("Go to slide") 
            and l not in ["Popular", "New", "Fair Price", "Great Price"]
        ]

        if not meaningful_lines:
            return None

        title_main = meaningful_lines[0]
        subtitle = meaningful_lines[1] if len(meaningful_lines) > 1 else ""
        full_title = f"{title_main} - {subtitle}".strip(" -")

        # Extract price string (e.g. S$14,500 or $12,000)
        price_raw = ""
        seller_type = "Dealer / Seller"
        country_code = None

        for line in meaningful_lines[1:]:
            if re.search(r"[\$€£]|SGD|USD|EUR|\d{3,}", line) and not price_raw and ("S$" in line or "$" in line or "€" in line or "£" in line):
                price_raw = line
            elif line in ["Private Seller", "Professional Dealer", "Verified Dealer"]:
                seller_type = line
            elif len(line) == 2 and line.isupper():
                country_code = line

        seller = SellerInfo(
            username=seller_type,
            first_name=f"Chrono24 Seller ({country_code})" if country_code else seller_type,
            profile_url=CHRONO24_BASE_URL
        )

        return WatchListing(
            listing_id=listing_id,
            title=full_title or title_main,
            price_raw=price_raw or "Price on request",
            price_sgd=clean_price(price_raw),
            condition="Pre-Owned / New (See Listing)",
            description=f"Listed on Chrono24 ({country_code or 'Global'}). Seller: {seller_type}",
            url=full_url,
            thumbnail_url=thumbnail_url,
            photo_urls=[thumbnail_url] if thumbnail_url else [],
            seller=seller,
            brand_keyword=brand_keyword or "Chrono24"
        )

    def scrape_by_query(
        self,
        query: str,
        sort: Optional[str] = "recent",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        max_pages: int = 1
    ) -> List[WatchListing]:
        """Scrape Chrono24 search results via Playwright."""
        all_listings: List[WatchListing] = []
        seen_ids = set()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            for pg in range(1, max_pages + 1):
                url = self._build_search_url(
                    query=query,
                    sort=sort,
                    min_price=min_price,
                    max_price=max_price,
                    page=pg
                )
                page.goto(url, wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(2500)

                # Scroll down slightly to ensure lazy images load
                page.evaluate("window.scrollBy(0, 800)")
                page.wait_for_timeout(1000)

                html = page.content()
                soup = BeautifulSoup(html, "html.parser")
                cards = soup.select(".wt-search-result, .article-item-container, .article-item, [class*=\"article-item\"]")

                for card in cards:
                    parsed = self.parse_card_html(card, brand_keyword=query)
                    if parsed and parsed.listing_id not in seen_ids:
                        seen_ids.add(parsed.listing_id)
                        all_listings.append(parsed)

            browser.close()

        return all_listings

    def scrape_by_url(self, direct_url: str, brand_keyword: Optional[str] = None) -> List[WatchListing]:
        """Scrape directly from any custom Chrono24 URL."""
        all_listings: List[WatchListing] = []
        seen_ids = set()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            page.goto(direct_url, wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(2500)

            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(1000)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(".wt-search-result, .article-item-container, .article-item, [class*=\"article-item\"]")

            for card in cards:
                parsed = self.parse_card_html(card, brand_keyword=brand_keyword)
                if parsed and parsed.listing_id not in seen_ids:
                    seen_ids.add(parsed.listing_id)
                    all_listings.append(parsed)

            browser.close()

        return all_listings
