import csv, re, os

SRC = "/Users/danielgiroux/kenbot/feeds/meta_used.csv"
OUT = "docs/feeds/meta_vehicle.csv"

ADDRESS_DEFAULT = "1887 83e rue, Saint-Georges, QC G6A 1M9"

def parse_year(title: str):
    m = re.search(r"(19|20)\d{2}", title or "")
    return m.group(0) if m else ""

def parse_make_model(title: str):
    # Exemple: "Jeep GLADIATOR SPORT WILLYS 2022"
    t = (title or "").strip()
    year = parse_year(t)
    t2 = re.sub(r"(19|20)\d{2}", "", t).strip()
    parts = t2.split()
    if not parts:
        return "", ""
    make = parts[0]
    model = " ".join(parts[1:]).strip()
    # model vide? on met le reste du title
    return make, model

def parse_km(desc: str):
    m = re.search(r"KM:\s*([0-9][0-9\s]*)", desc or "", re.IGNORECASE)
    if not m:
        return ""
    return re.sub(r"\s+", "", m.group(1))

def normalize_price(price: str):
    p = (price or "").strip()
    if not p:
        return ""  # Meta aime pas trop vide, mais mieux que fake
    # garde tel quel si déjà "xxxxx CAD"
    if "CAD" in p.upper():
        return p.replace(",", "").replace("  ", " ")
    # si c'est juste un nombre
    digits = re.sub(r"[^\d]", "", p)
    return f"{digits} CAD" if digits else ""

os.makedirs(os.path.dirname(OUT), exist_ok=True)

with open(SRC, newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    rows = list(r)

fieldnames = [
    "vehicle_id","make","model","year","mileage","price","url","image",
    "state_of_vehicle","address","body_style"
]

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()

    for x in rows:
        title = x.get("title","")
        make, model = parse_make_model(title)
        year = parse_year(title)
        mileage = parse_km(x.get("description",""))
        price = normalize_price(x.get("price",""))
        url = x.get("link","")
        image = x.get("image_link","")
        vehicle_id = x.get("id","")

        # condition -> state_of_vehicle
        state = (x.get("condition","") or "used").lower()
        state = "used" if "used" in state else state

        # Si pas de prix, tu peux soit laisser vide, soit skipper.
        # Ici je SKIP si pas de prix, sinon Meta va souvent capoter.
        if not price:
            continue

        w.writerow({
            "vehicle_id": vehicle_id,
            "make": make,
            "model": model,
            "year": year,
            "mileage": mileage,
            "price": price,
            "url": url,
            "image": image,
            "state_of_vehicle": state,
            "address": ADDRESS_DEFAULT,
            "body_style": ""
        })

print(f"[OK] Wrote {OUT}")
