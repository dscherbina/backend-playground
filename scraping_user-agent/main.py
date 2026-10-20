import csv
import random
import re
import sys
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
OUTPUT_FILE = Path("output") / "all_books.csv"
CACHE_NAME = "cache/http_cache"
CACHE_TTL = timedelta(days=1)
TIMEOUT = (10, 30)
PAUSE_RANGE = (1, 3)
EXPECTED_BOOKS = 1000

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

FIELDS = ["title", "price", "rating", "availability", "url"]


def build_session():
    Path(CACHE_NAME).parent.mkdir(parents=True, exist_ok=True)
    session = requests_cache.CachedSession(
        CACHE_NAME,
        backend="sqlite",
        expire_after=CACHE_TTL,
    )
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def parse_price(text):
    match = re.search(r"\d+(?:\.\d+)?", text or "")
    return float(match.group()) if match else None


def parse_rating(tag):
    if tag is None:
        return None
    for name in tag.get("class", []):
        if name in RATINGS:
            return RATINGS[name]
    return None


def select_text(parent, selector):
    tag = parent.select_one(selector)
    return tag.get_text(strip=True) if tag else None


def parse_book(article, page_url):
    link = article.select_one("h3 a")
    if link is None:
        return None
    title = (link.get("title") or link.get_text(strip=True) or "").strip()
    href = link.get("href")
    if not title or not href:
        return None
    return {
        "title": title,
        "price": parse_price(select_text(article, "p.price_color")),
        "rating": parse_rating(article.select_one("p.star-rating")),
        "availability": select_text(article, "p.availability"),
        "url": urljoin(page_url, href),
    }


def parse_page(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    books = []
    skipped = 0
    for article in soup.select("article.product_pod"):
        book = parse_book(article, page_url)
        if book is None:
            skipped += 1
            continue
        books.append(book)
    if skipped:
        print(f"warning: skipped {skipped} malformed items on {page_url}", file=sys.stderr)
    next_link = soup.select_one("li.next a[href]")
    next_url = urljoin(page_url, next_link["href"]) if next_link else None
    return books, next_url


def fetch(session, url):
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    if not getattr(response, "from_cache", False):
        time.sleep(random.uniform(*PAUSE_RANGE))
    return response


def scrape():
    session = build_session()
    all_books = []
    visited = set()
    url = START_URL
    page = 0
    while url:
        if url in visited:
            print(f"warning: already visited {url}, stopping pagination", file=sys.stderr)
            break
        visited.add(url)
        page += 1
        response = fetch(session, url)
        books, url = parse_page(response.content, response.url)
        all_books.extend(books)
        source = "cache" if getattr(response, "from_cache", False) else "network"
        print(f"page {page}: {len(books)} books ({source}), total {len(all_books)}")
    return all_books


def validate(books):
    if len(books) != EXPECTED_BOOKS:
        print(
            f"error: expected {EXPECTED_BOOKS} books, got {len(books)}; file not written",
            file=sys.stderr,
        )
        return False
    unique_urls = {book["url"] for book in books}
    if len(unique_urls) != len(books):
        print("error: duplicate book urls found; file not written", file=sys.stderr)
        return False
    return True


def save(books):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = OUTPUT_FILE.with_suffix(".csv.tmp")
    with tmp_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(books)
    tmp_file.replace(OUTPUT_FILE)


def main():
    started = time.perf_counter()
    books = scrape()
    if not validate(books):
        return 1
    save(books)
    elapsed = time.perf_counter() - started
    print(f"saved {len(books)} books to {OUTPUT_FILE} in {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())