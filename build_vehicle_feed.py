import csv
import re
from pathlib import Path

SRC = "/Users/danielgiroux/kenbot/feeds/meta_used.csv"
OUT = "docs/feeds/meta_vehicle.csv"

HEADERS = [
    "id","title","description","availability","condition",
    "price","link","image_link","brand","year"
]

def extract_year(title: str) -> str:
    if not title:
        return ""
    m = re.search(r"(19|20)\d{2}", title)
    return m.group(0) if m else ""

def extract_brand(title: str) -> str:
    if not title:
        return ""
    return title.split()[0].capitalize()

def clean_text(s: str) -> str:
    return (s or "").replace("\r", " ").replace("\n", " ").strip()

def main():
    if not Path(SRC).exists():
        raise SystemExit(f"❌ Source introuvable: {SRC}")

    Path("docs/feeds").mkdir(parents=True, exist_ok=True)

    with open(SRC, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()

        kept = 0
        skipped = 0

        for r in rows:
            title = clean_text(r.get("title", ""))
            year = extract_year(title)
            brand = extract_brand(title)

            row_out = {
                "id": r.get("vehicle_id") or r.get("id"),
                "title": title,
                "description": clean_text(r.get("description")) or f"{title} — Véhicule inspecté et prêt à partir.",
                "availability": "in stock",
                "condition": "used",
                "price": "1 CAD",   # ⚠️ prix minimal pour forcer Meta
                "link": r.get("url") or r.get("link"),
                "image_link": r.get("image") or r.get("image_link"),
                "brand": brand,
                "year": year,
            }

            # Champs minimum requis par Meta
            if not row_out["id"] or not row_out["title"] or not row_out["link"] or not row_out["image_link"]:
                skipped += 1
                continue

            w.writerow(row_out)
            kept += 1

    print("✅ meta_vehicle.csv généré avec fallback forcé")
    print(f"✅ Articles gardés: {kept} | ⛔ Ignorés: {skipped}")

if __name__ == "__main__":
    main()
