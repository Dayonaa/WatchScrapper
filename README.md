# ⌚ Multi-Platform Luxury Watch Scrapper

Project scraper data jam tangan branded/mewah (*Rolex, Patek Philippe, Audemars Piguet, Omega, Cartier, Tudor, dll.*) dari dua marketplace utama:
1. 🇸🇬 **Carousell Singapore** (`carousell.sg`)
2. 🌐 **Chrono24 Global / SG** (`chrono24.sg`)

Semua data hasil scraping otomatis diseragamkan ke dalam **skema data Pydantic yang 100% konsisten** dan diekspor ke **Excel (`.xlsx`)**, **CSV**, dan **JSON**.

---

## 📋 Daftar Isi
- [Persiapan & Instalasi](#-persiapan--instalasi)
- [Cheatsheet Perintah Scraper (CLI)](#-cheatsheet-perintah-scraper-cli)
  - [1. Scraping dari Carousell](#1-scraping-dari-carousell-default)
  - [2. Scraping dari Chrono24](#2-scraping-dari-chrono24)
  - [3. Gabung Kedua Website Sekaligus (Multi-Platform)](#3-gabung-kedua-website-sekaligus-multi-platform)
  - [4. Filter Kisaran Harga & Sorting](#4-filter-kisaran-harga--sorting)
  - [5. Batch Scraping Banyak Brand Sekaligus](#5-batch-scraping-banyak-brand-sekaligus)
  - [6. Scraping dari Link / URL Spesifik](#6-scraping-dari-link--url-spesifik)
  - [7. Pilihan Format Output & Folder](#7-pilihan-format-output--folder)
- [Struktur Data Output](#-struktur-data-output)
- [Penggunaan via Script Python (Python API)](#-penggunaan-via-script-python-python-api)
- [Struktur Direktori Project](#-struktur-direktori-project)

---

## 🛠️ Persiapan & Instalasi

Project ini dikelola menggunakan package manager modern **[`uv`](https://github.com/astral-sh/uv)** (cepat, andal, tanpa perlu setup manual virtualenv).

### 1. Masuk ke Folder Project
```bash
cd WatchScrapper
```

### 2. Install Dependensi & Browser Playwright
```bash
# Sinkronisasi environment & dependensi
uv sync

# Install browser Chromium untuk Playwright (diperlukan untuk Chrono24 & Deep mode)
uv run playwright install chromium
```

---

## 🚀 Cheatsheet Perintah Scraper (CLI)

Semua perintah dijalankan menggunakan prefix `uv run python main.py`.

### 1. Scraping dari Carousell (Default)

> **Catatan**: Mode ini menggunakan *Fast HTTP State Extraction* (sangat cepat, 1–2 detik langsung dapat 40–50 listings lengkap).

```bash
# Scrape jam tangan Rolex (default)
uv run python main.py

# Scrape brand atau model tertentu
uv run python main.py --site carousell --query "omega speedmaster"
uv run python main.py --site carousell --query "cartier santos"
uv run python main.py --site carousell --query "tudor black bay"
```

Jika ingin Carousell membuka browser dan melakukan *infinite scroll* otomatis ke bawah:
```bash
uv run python main.py --site carousell --query "rolex" --deep
```

---

### 2. Scraping dari Chrono24

> **Catatan**: Menggunakan integrasi Playwright untuk scraping marketplace global Chrono24.

```bash
# Scrape Rolex Submariner dari Chrono24
uv run python main.py --site chrono24 --query "rolex submariner"

# Scrape Patek Philippe Nautilus dari Chrono24
uv run python main.py --site chrono24 --query "patek philippe nautilus"

# Scrape Audemars Piguet Royal Oak hingga 3 Halaman
uv run python main.py --site chrono24 --query "audemars piguet royal oak" --pages 3
```

---

### 3. Gabung Kedua Website Sekaligus (Multi-Platform)

Fitur `--site all` akan otomatis mengambil data dari **Carousell DAN Chrono24** lalu menggabungkannya ke dalam 1 file output yang sama:

```bash
uv run python main.py --site all --query "omega seamaster"
uv run python main.py --site all --query "cartier tank"
```

---

### 4. Filter Kisaran Harga & Sorting

Kamu bisa menyaring rentang budget harga (dalam SGD) serta mengurutkan hasil:

```bash
# Filter Rolex harga SGD 10.000 s/d 50.000 dengan urutan harga termurah (price_asc)
uv run python main.py --site chrono24 --query "rolex" --min-price 10000 --max-price 50000 --sort price_asc

# Filter Tudor harga SGD 3.000 s/d 8.000 dengan urutan terbaru (recent)
uv run python main.py --site carousell --query "tudor" --min-price 3000 --max-price 8000 --sort recent
```

**Pilihan Opsi Sorting (`--sort`)**:
- `recent` : Listing paling baru (Default)
- `price_asc` : Harga terendah ke tertinggi
- `price_desc` : Harga tertinggi ke terendah
- `best_match` : Relevansi pencarian terbaik

---

### 5. Batch Scraping Banyak Brand Sekaligus

```bash
# Scraping otomatis 15 Brand Mewah Populer (Rolex, Patek, AP, Omega, Cartier, Tudor, IWC, Breitling, dll.)
uv run python main.py --all-brands

# Scraping beberapa brand pilihanmu saja
uv run python main.py --brands rolex omega tudor cartier "patek philippe"
```

---

### 6. Scraping dari Link / URL Spesifik

Jika punya URL pencarian atau kategori kustom dari browser, langsung masukkan ke argumen `--url`:

```bash
# URL Carousell
uv run python main.py --url "https://www.carousell.sg/categories/luxury-20/luxury-watches-256/?search=rolex&t-search_query_source=ss_dropdown"

# URL Chrono24
uv run python main.py --url "https://www.chrono24.sg/rolex/index.htm"
```

---

### 7. Pilihan Format Output & Folder

Secara default, scraper akan membuat 3 format file sekaligus di folder `data/`. Kamu bisa memilih format tertentu:

```bash
# Hanya simpan format Excel (.xlsx)
uv run python main.py --site chrono24 --query "rolex" --format excel

# Hanya simpan format CSV (.csv)
uv run python main.py --site carousell --query "omega" --format csv

# Custom folder penyimpanan
uv run python main.py --query "rolex" --out-dir "hasil_scraping"
```

---

## 📊 Struktur Data Output

Setiap baris data (di Excel/CSV) dan item di JSON dijamin memiliki kolom standar berikut:

| Nama Kolom | Tipe Data | Deskripsi | Contoh Nilai |
| :--- | :--- | :--- | :--- |
| `listing_id` | `String` | ID unik listing produk | `"1460809794"` / `"id43078533"` |
| `title` | `String` | Judul / nama jam tangan | `"Brand New 2026 Rolex 126500LN Daytona..."` |
| `brand` | `String` | Keyword brand pencarian | `"rolex"` / `"omega"` |
| `price_raw` | `String` | Tampilan harga asli string | `"S$37,990"` |
| `price_sgd` | `Float` | Angka harga bersih (siap dihitung/agregasi) | `37990.0` |
| `condition` | `String` | Kondisi jam | `"Brand new"`, `"Like new"`, `"Lightly used"` |
| `seller_username` | `String` | Username penjual / tipe dealer | `"bellewatchsg"` / `"Private Seller"` |
| `seller_name` | `String` | Nama profil penjual | `"Belle Watch"` / `"Chrono24 Seller (SG)"` |
| `seller_url` | `String` | Link profil penjual | `"https://www.carousell.sg/u/bellewatchsg/"` |
| `url` | `String` | URL langsung ke halaman produk | `"https://www.carousell.sg/p/1460809794"` |
| `thumbnail_url` | `String` | Link gambar cover produk | `"https://media.karousell.com/..."` |
| `photo_urls` | `Array/Str` | Kumpulan URL semua foto | `["https://...photo1.jpg", ...]` |
| `description` | `String` | Deskripsi lengkap listing | `"Case Size: 40MM, Box & Papers..."` |
| `likes_count` | `Integer` | Jumlah likes / wishlist | `12` |
| `time_created` | `Datetime` | Waktu listing dibuat | `"2026-09-10 09:30:00"` |
| `scraped_at` | `Datetime` | Waktu scraping dilakukan | `"2026-09-10 16:46:17"` |

---

## 💻 Penggunaan via Script Python (Python API)

Jika ingin memanggil scraper dari dalam script Python lain (misalnya untuk integrasi database atau dashboard):

```python
from scraper import CarousellScraper, Chrono24Scraper, export_to_excel, export_to_json

# 1. Scraping dari Carousell
carousell = CarousellScraper()
rolex_listings = carousell.scrape_by_query("rolex", sort="recent")

# 2. Scraping dari Chrono24
chrono24 = Chrono24Scraper()
patek_listings = chrono24.scrape_by_query("patek philippe nautilus", max_pages=2)

# 3. Gabungkan hasil
all_watches = rolex_listings + patek_listings

# 4. Simpan ke Excel & JSON
export_to_excel(all_watches, "data/koleksi_jam.xlsx")
export_to_json(all_watches, "data/koleksi_jam.json")

print(f"Berhasil mengumpulkan {len(all_watches)} jam tangan!")
```

---

## 📁 Struktur Direktori Project

```text
WatchScrapper/
├── main.py                # Entrypoint CLI interaktif & argumen parser
├── pyproject.toml         # Konfigurasi dependensi uv
├── README.md              # Dokumentasi & panduan penggunaan
├── scraper/
│   ├── __init__.py        # Exporter package interface
│   ├── models.py          # Schema data Pydantic (WatchListing, SellerInfo)
│   ├── parser.py          # Logika parsing & pembersihan teks/harga
│   ├── carousell.py       # Engine scraper Carousell Singapore
│   ├── chrono24.py        # Engine scraper Chrono24 (Playwright)
│   └── exporter.py        # Modul ekspor ke Excel, CSV, dan JSON
└── data/                  # Folder otomatis tempat file hasil scraping tersimpan
```
