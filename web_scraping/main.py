import csv
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

URL = "https://quotes.toscrape.com/"
HEADERS = ["text", "author", "tags", "author_url"]


def scrape_first_page(url: str = URL) -> list[list[str]]:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    rows = []
    for quote in soup.select("div.quote"):
        text = quote.select_one("span.text").get_text(strip=True)
        author = quote.select_one("small.author").get_text(strip=True)
        tags = ", ".join(tag.get_text(strip=True) for tag in quote.select("a.tag"))
        href = quote.select_one("a[href^='/author/']")["href"]
        author_url = urljoin(url, href)
        rows.append([text, author, tags, author_url])
    return rows


def save_csv(rows: list[list[str]], path: str = "quotes.csv") -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(rows)


def save_xlsx(rows: list[list[str]], path: str = "quotes.xlsx") -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "quotes"
    ws.append(HEADERS)
    for row in rows:
        ws.append(row)
    wb.save(path)


def main() -> None:
    rows = scrape_first_page()
    save_csv(rows)
    save_xlsx(rows)
    print(f"Збережено цитат: {len(rows)} -> quotes.csv, quotes.xlsx")


if __name__ == "__main__":
    main()