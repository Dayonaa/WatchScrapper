import urllib.parse
import urllib.request
import time
from typing import List, Optional, Dict, Any
from .models import WatchListing
from .parser import extract_listings_from_html

LUXURY_WATCHES_URL = "https://www.carousell.sg/categories/luxury-20/luxury-watches-256/"

POPULAR_WATCH_BRANDS = [
    "Rolex",
    "Patek Philippe",
    "Audemars Piguet",
    "Omega",
    "Tudor",
    "Cartier",
    "Richard Mille",
    "IWC",
    "Breitling",
    "Panerai",
    "Vacheron Constantin",
    "Grand Seiko",
    "Tag Heuer",
    "Jaeger-LeCoultre",
    "Hublot"
]

SORT_MAP = {
    "best_match": None,
    "recent": "3",
    "price_asc": "2",
    "price_desc": "1",
    "time_created": "3"
}

class CarousellScraper:
    def __init__(self, user_agent: Optional[str] = None, delay: float = 1.0):
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.delay = delay

    def _build_search_url(
        self,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        category_url: str = LUXURY_WATCHES_URL
    ) -> str:
        params = {}
        if query:
            params["search"] = query
            params["t-search_query_source"] = "ss_dropdown"
        
        if sort and sort in SORT_MAP and SORT_MAP[sort]:
            params["sort_by"] = SORT_MAP[sort]
        elif sort and sort in ["1", "2", "3"]:
            params["sort_by"] = sort

        if min_price is not None:
            params["price_start"] = str(int(min_price))
        if max_price is not None:
            params["price_end"] = str(int(max_price))

        if params:
            query_string = urllib.parse.urlencode(params)
            base = category_url.rstrip("?")
            if "?" in base:
                return f"{base}&{query_string}"
            return f"{base}?{query_string}"
        return category_url

    def fetch_page_html(self, url: str) -> str:
        """Fetch raw HTML of a Carousell page with headers."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.carousell.sg/"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="ignore")

    def scrape_by_query(
        self,
        query: str,
        sort: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[WatchListing]:
        """Scrape watch listings for a specific brand or search term."""
        url = self._build_search_url(
            query=query,
            sort=sort,
            min_price=min_price,
            max_price=max_price
        )
        html = self.fetch_page_html(url)
        listings = extract_listings_from_html(html, brand_keyword=query)
        return listings

    def scrape_by_url(self, target_url: str, brand_keyword: Optional[str] = None) -> List[WatchListing]:
        """Scrape directly from any custom Carousell search URL."""
        html = self.fetch_page_html(target_url)
        return extract_listings_from_html(html, brand_keyword=brand_keyword)

    def scrape_brands(
        self,
        brands: List[str],
        sort: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        callback = None
    ) -> List[WatchListing]:
        """Scrape multiple luxury watch brands in batch."""
        all_listings: List[WatchListing] = []
        seen_ids = set()

        for idx, brand in enumerate(brands):
            try:
                results = self.scrape_by_query(
                    query=brand,
                    sort=sort,
                    min_price=min_price,
                    max_price=max_price
                )
                new_items = []
                for item in results:
                    if item.listing_id not in seen_ids:
                        seen_ids.add(item.listing_id)
                        new_items.append(item)
                        all_listings.append(item)
                
                if callback:
                    callback(brand, len(new_items), len(all_listings))
                
                if idx < len(brands) - 1:
                    time.sleep(self.delay)
            except Exception as e:
                if callback:
                    callback(brand, 0, len(all_listings), error=str(e))

        return all_listings

    def scrape_playwright_deep(
        self,
        url_or_query: str,
        scroll_count: int = 5,
        brand_keyword: Optional[str] = None
    ) -> List[WatchListing]:
        """Scrape using Playwright for deep continuous loading if needed."""
        from playwright.sync_api import sync_playwright

        if url_or_query.startswith("http://") or url_or_query.startswith("https://"):
            url = url_or_query
        else:
            url = self._build_search_url(query=url_or_query)
            brand_keyword = brand_keyword or url_or_query

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=self.user_agent)
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            for _ in range(scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)

            content = page.content()
            browser.close()

        return extract_listings_from_html(content, brand_keyword=brand_keyword)
