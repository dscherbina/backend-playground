import csv
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
OUTPUT_FILE = Path("output") / "all_books.csv"
CACHE_NAME = "cache/http_cache"
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
        expire_after=requests_cache.NEVER_EXPIRE,
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
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def parse_rating(tag):
    classes = tag.get("class", []) if tag else []
    for name in classes:
        if name in RATINGS:
            return RATINGS[name]
    return None


def parse_page(html, page_url):
    soup = BeautifulSoup(html, "html.parser", from_encoding="utf-8")
    books = []
    for article in soup.select("article.product_pod"):
        link = article.select_one("h3 a")
        books.append(
            {
                "title": link["title"].strip(),
                "price": parse_price(article.select_one("p.price_color").get_text()),
                "rating": parse_rating(article.select_one("p.star-rating")),
                "availability": article.select_one("p.availability").get_text(strip=True),
                "url": urljoin(page_url, link["href"]),
            }
        )
    next_link = soup.select_one("li.next a")
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
    url = START_URL
    page = 0
    while url:
        page += 1
        response = fetch(session, url)
        books, url = parse_page(response.content, response.url)
        all_books.extend(books)
        source = "cache" if getattr(response, "from_cache", False) else "network"
        print(f"page {page}: {len(books)} books ({source}), total {len(all_books)}")
    return all_books


def save(books):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(books)


def main():
    started = time.perf_counter()
    books = scrape()
    save(books)
    elapsed = time.perf_counter() - started
    print(f"saved {len(books)} books to {OUTPUT_FILE} in {elapsed:.1f}s")
    if len(books) != EXPECTED_BOOKS:
        print(f"warning: expected {EXPECTED_BOOKS} books", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())