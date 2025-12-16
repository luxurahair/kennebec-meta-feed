#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE = "https://www.kennebecdodge.ca"
LIST = BASE + "/fr/inventaire-occasion"
OUT_DIR = Path(__file__).resolve().parent / "docs"
OUT_DIR.mkdir(exist_ok=True)
OUT_CSV = OUT_DIR / "meta_used.csv"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean_int(s: str) -> int:
    s = re.sub(r"[^\d]", "", s or "")
    return int(s) if s else 0

def list_detail_urls(max_pages: int = 10) -> list[str]:
    urls = []
    seen = set()
    for page in range(1, max_pages + 1):
        url = LIST if page == 1 else f"{LIST}?page={page}"
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        found = 0
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            href_no_q = href.split("?")[0]
            # fiches véhicules: ...-id12345678
            if re.search(r"/fr/inventaire-occasion/.+-id\d+$", href_no_q, flags=re.I):
                full = urljoin(BASE, href_no_q)
                if full not in seen:
                    seen.add(full)
                    urls.append(full)
                    found += 1

        if found == 0:
            break
    return urls

def parse_detail(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # ID stable Meta = le -id#### à la fin
    meta_id = url.split("-id")[-1]

    # Title: h1 sinon title
    h1 = soup.select_one("h1")
    title = (h1.get_text(" ", strip=True) if h1 else "") or soup.title.get_text(" ", strip=True)
    title = re.sub(r"\s+\|\s+.*$", "", title).strip()

    # Image: og:image sinon première image plausible
    og = soup.select_one('meta[property="og:image"]')
    image_link = og.get("content", "").strip() if og else ""
    if not image_link:
        img = soup.select_one("img[src], img[data-src]")
        if img:
            image_link = (img.get("data-src") or img.get("src") or "").strip()
    if image_link:
        image_link = urljoin(BASE, image_link)

    text = soup.get_text("\n")
    text = re.sub(r"[ \t]+", " ", text)

    # Prix: essaie plusieurs patterns
    price = 0
    m = re.search(r"(\d[\d\s]{3,})\s*\$", text)
    if m:
        price = clean_int(m.group(1))
    if price == 0:
        m = re.search(r'"price"\s*:\s*"?(?P<p>\d{4,7})"?', r.text, flags=re.I)
        if m:
            price = clean_int(m.group("p"))
    if price == 0:
        m = re.search(r'"offerPrice"\s*:\s*"?(?P<p>\d{4,7})"?', r.text, flags=re.I)
        if m:
            price = clean_int(m.group("p"))

    # KM
    km = 0
    m = re.search(r"(\d[\d\s]{2,})\s*km", text, flags=re.I)
    if m:
        km = clean_int(m.group(1))

    desc = f"{title}\nKM: {km}".strip()

    return {
        "id": meta_id,
        "title": title[:150],
        "description": desc[:5000],
        "availability": "in stock",
        "condition": "used",
        "price": (f"{price} CAD" if price > 0 else ""),
        "link": url,
        "image_link": image_link,
        "brand": "Kennebec Dodge Chrysler",
    }

def main():
    detail_urls = list_detail_urls(max_pages=10)
    rows = []
    for u in detail_urls:
        try:
            rows.append(parse_detail(u))
        except Exception as e:
            print(f"[CAT] skip {u} ({e})")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["id","title","description","availability","condition","price","link","image_link","brand"],
        )
        w.writeheader()
        w.writerows(rows)

    print(f"[CAT] ✅ Feed généré: {OUT_CSV} ({len(rows)} véhicules)")

if __name__ == "__main__":
    main()

