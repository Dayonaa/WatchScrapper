import argparse
import sys
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from scraper.carousell import CarousellScraper, POPULAR_WATCH_BRANDS
from scraper.chrono24 import Chrono24Scraper
from scraper.exporter import export_to_csv, export_to_excel, export_to_json

console = Console()

def display_banner(site="all"):
    site_names = {
        "carousell": "Carousell Singapore",
        "chrono24": "Chrono24 Global/SG",
        "all": "Carousell + Chrono24"
    }
    banner_text = (
        f"[bold cyan]⌚ Multi-Platform Luxury Watch Scrapper[/bold cyan] [yellow]({site_names.get(site, site)})[/yellow]\n"
        "[dim]Scrapes luxury watches (Rolex, Patek Philippe, Audemars Piguet, Omega, etc.) "
        "with consistent schema and export to Excel/CSV/JSON.[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan"))

def display_results_table(listings, limit=10):
    if not listings:
        console.print("[yellow]No listings found.[/yellow]")
        return

    table = Table(title=f"Sample Results (Showing up to {min(limit, len(listings))} of {len(listings)} items)", border_style="blue")
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="white", max_width=45, overflow="ellipsis")
    table.add_column("Price (SGD)", justify="right", style="green")
    table.add_column("Condition", style="magenta")
    table.add_column("Seller", style="yellow")
    table.add_column("URL", style="dim underline", max_width=40, overflow="ellipsis")

    for i, item in enumerate(listings[:limit], 1):
        price_display = item.price_raw or (f"S${item.price_sgd:,.0f}" if item.price_sgd else "N/A")
        seller_display = item.seller.username if item.seller and item.seller.username else "-"
        table.add_row(
            str(i),
            item.title,
            price_display,
            item.condition or "Unknown",
            seller_display,
            item.url
        )

    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Multi-Platform Luxury Watch Scrapper")
    parser.add_argument("--site", choices=["carousell", "chrono24", "all"], default="carousell", help="Target website (default: carousell)")
    parser.add_argument("-q", "--query", type=str, default="rolex", help="Brand or search keyword (default: rolex)")
    parser.add_argument("--url", type=str, help="Direct search/category URL to scrape")
    parser.add_argument("--all-brands", action="store_true", help="Scrape all popular luxury watch brands in batch")
    parser.add_argument("--brands", nargs="+", help="Custom list of brands to scrape (e.g. rolex omega tudor)")
    parser.add_argument("--sort", choices=["best_match", "recent", "price_asc", "price_desc"], default="recent", help="Sort order (default: recent)")
    parser.add_argument("--min-price", type=float, help="Minimum price in SGD")
    parser.add_argument("--max-price", type=float, help="Maximum price in SGD")
    parser.add_argument("--format", choices=["all", "excel", "csv", "json"], default="all", help="Export format (default: all)")
    parser.add_argument("--out-dir", type=str, default="data", help="Output directory (default: data)")
    parser.add_argument("--deep", action="store_true", help="Use Playwright deep continuous scrolling (Carousell)")
    parser.add_argument("--pages", type=int, default=1, help="Max pages to scrape (Chrono24, default: 1)")

    args = parser.parse_args()
    display_banner(site=args.site)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(args.out_dir, exist_ok=True)

    listings = []

    # Detect site from URL if provided
    site = args.site
    if args.url:
        if "chrono24" in args.url:
            site = "chrono24"
        elif "carousell" in args.url:
            site = "carousell"

    # --- CHRONO24 SCRAPER ---
    if site == "chrono24":
        chrono_scraper = Chrono24Scraper()
        if args.url:
            console.print(f"[bold green]Scraping Chrono24 URL:[/bold green] {args.url}")
            with console.status("[bold green]Scraping Chrono24 via Playwright...[/bold green]", spinner="dots"):
                listings = chrono_scraper.scrape_by_url(args.url, brand_keyword=args.query)
            prefix = "chrono24_custom"
        else:
            brand_name = args.query.strip()
            console.print(f"[bold cyan]Scraping Chrono24 for:[/bold cyan] [bold yellow]{brand_name}[/bold yellow] (sort: {args.sort}, pages: {args.pages})")
            with console.status(f"[bold green]Fetching Chrono24 ({brand_name})...[/bold green]", spinner="dots"):
                listings = chrono_scraper.scrape_by_query(
                    query=brand_name,
                    sort=args.sort,
                    min_price=args.min_price,
                    max_price=args.max_price,
                    max_pages=args.pages
                )
            prefix = f"chrono24_{brand_name.lower().replace(' ', '_')}"

    # --- CAROUSELL SCRAPER ---
    elif site == "carousell":
        carousell_scraper = CarousellScraper()

        if args.url:
            console.print(f"[bold green]Fetching Carousell URL:[/bold green] {args.url}")
            with console.status("[bold green]Scraping URL...[/bold green]", spinner="dots"):
                listings = carousell_scraper.scrape_by_url(args.url, brand_keyword=args.query)
            prefix = "carousell_custom"

        elif args.all_brands or args.brands:
            target_brands = args.brands if args.brands else POPULAR_WATCH_BRANDS
            console.print(f"[bold cyan]Batch scraping {len(target_brands)} luxury brands on Carousell...[/bold cyan]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Scraping brands...", total=len(target_brands))
                
                def progress_callback(brand, count, total_so_far, error=None):
                    if error:
                        console.print(f"[red]Failed {brand}: {error}[/red]")
                    else:
                        progress.console.print(f"  ✓ [bold]{brand}[/bold]: found {count} items (total: {total_so_far})")
                    progress.advance(task)

                listings = carousell_scraper.scrape_brands(
                    brands=target_brands,
                    sort=args.sort,
                    min_price=args.min_price,
                    max_price=args.max_price,
                    callback=progress_callback
                )
            prefix = "carousell_luxury_brands_all"

        else:
            brand_name = args.query.strip()
            console.print(f"[bold cyan]Scraping Carousell for:[/bold cyan] [bold yellow]{brand_name}[/bold yellow] (sort: {args.sort})")
            
            if args.deep:
                console.print("[dim]Using Playwright deep browser automation...[/dim]")
                with console.status("[bold green]Running Playwright deep scroll...[/bold green]", spinner="dots"):
                    listings = carousell_scraper.scrape_playwright_deep(brand_name, scroll_count=5)
            else:
                with console.status("[bold green]Scraping listings...[/bold green]", spinner="dots"):
                    listings = carousell_scraper.scrape_by_query(
                        query=brand_name,
                        sort=args.sort,
                        min_price=args.min_price,
                        max_price=args.max_price
                    )
            prefix = f"carousell_{brand_name.lower().replace(' ', '_')}"

    # --- ALL PLATFORMS COMBINED ---
    elif site == "all":
        brand_name = args.query.strip()
        console.print(f"[bold cyan]Scraping ALL platforms for:[/bold cyan] [bold yellow]{brand_name}[/bold yellow]")
        
        carousell_scraper = CarousellScraper()
        chrono_scraper = Chrono24Scraper()

        with console.status("[bold green]1/2 Scraping Carousell...[/bold green]", spinner="dots"):
            carousell_items = carousell_scraper.scrape_by_query(
                query=brand_name,
                sort=args.sort,
                min_price=args.min_price,
                max_price=args.max_price
            )
            console.print(f"  ✓ Carousell: found {len(carousell_items)} items")

        with console.status("[bold green]2/2 Scraping Chrono24...[/bold green]", spinner="dots"):
            chrono_items = chrono_scraper.scrape_by_query(
                query=brand_name,
                sort=args.sort,
                min_price=args.min_price,
                max_price=args.max_price,
                max_pages=args.pages
            )
            console.print(f"  ✓ Chrono24: found {len(chrono_items)} items")

        listings = carousell_items + chrono_items
        prefix = f"all_platforms_{brand_name.lower().replace(' ', '_')}"

    if not listings:
        console.print("[bold red]No listings could be retrieved.[/bold red]")
        sys.exit(1)

    console.print(f"\n[bold green]✓ Successfully scraped {len(listings)} luxury watch listings![/bold green]\n")
    display_results_table(listings, limit=10)

    # Exporting
    console.print("\n[bold cyan]Exporting data...[/bold cyan]")
    files_created = []

    if args.format in ["all", "excel"]:
        xlsx_path = os.path.join(args.out_dir, f"{prefix}_{timestamp_str}.xlsx")
        export_to_excel(listings, xlsx_path)
        files_created.append(xlsx_path)

    if args.format in ["all", "csv"]:
        csv_path = os.path.join(args.out_dir, f"{prefix}_{timestamp_str}.csv")
        export_to_csv(listings, csv_path)
        files_created.append(csv_path)

    if args.format in ["all", "json"]:
        json_path = os.path.join(args.out_dir, f"{prefix}_{timestamp_str}.json")
        export_to_json(listings, json_path)
        files_created.append(json_path)

    for f in files_created:
        console.print(f"  💾 Saved: [bold green]{f}[/bold green]")

if __name__ == "__main__":
    main()
