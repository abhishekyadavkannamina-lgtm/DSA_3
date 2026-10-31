"""
build_dataset.py
================
Reads the three raw CSV files in data/raw/ and produces:
  - data/listings.csv       (all listings, real + simulated)
  - data/cart_data.json     (product/seller price matrix for Smart Cart)
  - data/flow_data.json     (orders + seller stock for Order Assignment)

Run:  python data/build_dataset.py
"""

import re
import json
import random
import pathlib
import pandas as pd
import numpy as np

# ── Exchange rates to INR (edit as needed) ─────────────────────────────────
FX = {
    "USD": 83.5,
    "EUR": 91.2,
    "GBP": 106.0,
    "INR": 1.0,
}

ROOT   = pathlib.Path(__file__).parent
RAW    = ROOT / "raw"
random.seed(42)
np.random.seed(42)

# ── Simulated sellers and title-style templates ────────────────────────────
SELLERS = ["QuickKart", "MegaMart", "ShopEase", "BazaarHub", "Croma"]

def _messy(title: str, style: int) -> str:
    """Apply a random title style variation to a clean title."""
    t = title
    if style == 0:
        t = t.upper()
    elif style == 1:
        t = t.lower().replace(" ", "-")
    elif style == 2:
        t = re.sub(r"(\d+)\s*(GB|gb|Gb)", lambda m: f"{m.group(1)}GB", t)
    elif style == 3:
        t = t.replace(" ", "").title()
    elif style == 4:
        t = re.sub(r"(\d+)\s*(GB|gb|Gb)", lambda m: f"{m.group(1)} gb", t, flags=re.I)
        t = t + " (Refurbished)"
    elif style == 5:
        t = t.replace("iPhone", "iphone").replace("Samsung", "SAMSUNG")
    else:
        t = t + " - New"
    return t


# ══════════════════════════════════════════════════════════════════════
#  LOAD SOURCES
# ══════════════════════════════════════════════════════════════════════

def load_gsmarena() -> pd.DataFrame:
    df = pd.read_csv(RAW / "gsmarena.csv")
    # Columns: phone_brand, phone_model, store, price, currency, storage, ...
    df = df.rename(columns={"phone_brand": "brand", "phone_model": "title",
                             "store": "seller", "price": "price_raw",
                             "currency": "currency", "storage": "storage_gb"})
    df = df[["brand", "title", "seller", "price_raw", "currency", "storage_gb"]].dropna(subset=["price_raw"])
    df["price_raw"] = pd.to_numeric(df["price_raw"], errors="coerce")
    df["currency"]  = df["currency"].str.upper().str.strip()
    df["price_inr"] = df.apply(
        lambda r: round(r["price_raw"] * FX.get(r["currency"], 1.0)), axis=1)
    df["source"] = "gsmarena"
    df["stock"]  = np.random.randint(2, 15, len(df))
    return df[["source", "seller", "title", "brand", "price_inr", "stock", "storage_gb"]].dropna(subset=["price_inr"])


def load_flipkart() -> pd.DataFrame:
    df = pd.read_csv(RAW / "flipkart.csv")
    # Columns: title, brand, selling_price, currency, ...
    df = df.rename(columns={"selling_price": "price_raw"})
    df = df[["title", "brand", "price_raw"]].dropna()
    df["price_raw"] = pd.to_numeric(df["price_raw"], errors="coerce")
    df = df.dropna(subset=["price_raw"])
    df["price_inr"] = df["price_raw"].round().astype(int)
    df["source"]    = "flipkart"
    df["seller"]    = "Flipkart"
    df["stock"]     = np.random.randint(1, 20, len(df))

    # Extract storage from title e.g. "64 GB"
    def _storage(t):
        m = re.search(r"(\d+)\s*GB", str(t), re.I)
        return int(m.group(1)) if m else np.nan
    df["storage_gb"] = df["title"].apply(_storage)

    return df[["source", "seller", "title", "brand", "price_inr", "stock", "storage_gb"]]


def load_cellphones() -> pd.DataFrame:
    df = pd.read_csv(RAW / "cellphones.csv")
    # Columns: brand, model, internal memory (GB), price (USD)
    df = df.rename(columns={"model": "model_name", "internal memory": "storage_gb", "price": "price_usd"})
    df = df[["brand", "model_name", "storage_gb", "price_usd"]].dropna()
    df["price_usd"] = pd.to_numeric(df["price_usd"], errors="coerce")
    df = df.dropna(subset=["price_usd"])

    rows = []
    for _, r in df.iterrows():
        title = f"{r['brand']} {r['model_name']} {int(r['storage_gb'])}GB"
        for seller, fx_mult in [("Amazon US", 1.0), ("Best Buy", 1.02)]:
            rows.append({
                "source": "cellphones",
                "seller": seller,
                "title": title,
                "brand": r["brand"],
                "price_inr": round(r["price_usd"] * fx_mult * FX["USD"]),
                "stock": random.randint(3, 12),
                "storage_gb": int(r["storage_gb"]),
            })
    return pd.DataFrame(rows)

def load_smartphones_csv() -> pd.DataFrame:
    path = ROOT / "../../Downloads/smartphones.csv"
    if not path.exists(): return pd.DataFrame()
    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        br = str(r.get("Brand", ""))
        mo = str(r.get("Model", ""))
        title = str(r.get("Smartphone", f"{br} {mo}"))
        
        try:
            price = float(r.get("Final Price", 0)) * FX["EUR"] # Assuming EUR or close
        except:
            price = 0.0
            
        storage = r.get("Storage", 128)
        if pd.isna(storage) or str(storage).lower() == "none": storage = 128
        try: storage = int(storage)
        except: storage = 128
        
        rows.append({
            "source": "smartphones_csv",
            "seller": random.choice(["Amazon DE", "Croma", "Flipkart", "QuickKart"]),
            "title": title,
            "brand": br,
            "price_inr": round(price),
            "stock": random.randint(1, 20),
            "storage_gb": storage
        })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════
#  ASSIGN GROUND TRUTH  (true_product_id)
# ══════════════════════════════════════════════════════════════════════

# Phones chosen to appear across sources — (brand_keyword, model_keyword, storage_gb)
CANONICAL = [
    ("apple",   "iphone se",  128),
    ("apple",   "iphone se",  256),
    ("apple",   "iphone 12",  128),
    ("apple",   "iphone 12",  256),
    ("apple",   "iphone 13",  128),
    ("apple",   "iphone 13",  256),
    ("apple",   "iphone 14",  128),
    ("apple",   "iphone 14",  256),
    ("apple",   "iphone 14 pro", 256),
    ("apple",   "iphone x",   256),
    ("samsung", "galaxy a13",  64),
    ("samsung", "galaxy a13", 128),
    ("samsung", "galaxy a53", 128),
    ("samsung", "galaxy s21", 128),
    ("samsung", "galaxy s21", 256),
    ("samsung", "galaxy s22", 128),
    ("samsung", "galaxy s22", 256),
    ("samsung", "galaxy s23", 256),
    ("samsung", "galaxy s24", 256),   # flagship — our demo pair
    ("samsung", "galaxy s24 ultra", 256),  # near-miss
    ("oneplus", "nord ce",    128),
    ("oneplus", "10 pro",     256),
    ("poco",    "m4 pro",     128),
    ("poco",    "c31",         64),
    ("poco",    "x4 pro",     128),
    ("redmi",   "note 11",     64),
    ("redmi",   "note 11",    128),
    ("realme",  "9 pro",      128),
    ("motorola","moto g",      64),
    ("motorola","moto g",     128),
]


def _matches_canonical(title: str, brand: str, storage, cano) -> bool:
    cb, cm, cs = cano
    t_low = str(title).lower()
    b_low = str(brand).lower()
    if cb not in b_low and cb not in t_low:
        return False
    if cm not in t_low:
        return False
    if pd.notna(storage):
        if abs(int(storage) - cs) > 2:
            return False
    else:
        # storage unknown — only match if storage is not discriminating
        if cs != 0:
            return False
    return True


def assign_ground_truth(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["true_product_id"] = pd.Series(dtype="object")
        return df
    df = df.copy()
    df["true_product_id"] = "UNMATCHED"
    for idx, (cb, cm, cs) in enumerate(CANONICAL):
        pid = f"P{idx+1:03d}"
        mask = df.apply(
            lambda r: _matches_canonical(r["title"], r.get("brand", ""), r.get("storage_gb", np.nan), (cb, cm, cs)),
            axis=1
        )
        df.loc[mask, "true_product_id"] = pid
    return df


# ══════════════════════════════════════════════════════════════════════
#  SIMULATED LISTINGS
# ══════════════════════════════════════════════════════════════════════

DEMO_PHONES = [
    ("Samsung", "Galaxy S24",    256, "Black",  68999),
    ("Samsung", "Galaxy S24",    256, "White",  69499),
    ("Samsung", "Galaxy S24",    128, "Black",  59999),   # near-miss: 128 vs 256
    ("Samsung", "Galaxy S24 Ultra", 256, "Black", 124999), # near-miss: ultra
    ("Apple",   "iPhone 15",     128, "Blue",   79999),
    ("Apple",   "iPhone 15",     256, "Blue",   89999),   # near-miss: 128 vs 256
    ("Apple",   "iPhone 15 Pro", 256, "Black",  134999),  # near-miss: pro
    ("OnePlus", "12",            256, "Green",  64999),
    ("Redmi",   "Note 13 Pro",   128, "Purple", 24999),
    ("Samsung", "Galaxy A54",    128, "Lime",   38999),
    ("Google",  "Pixel 8",       128, "Obsidian", 38999),
    ("Google",  "Pixel 8 Pro",   128, "Bay",      99999),
    ("Google",  "Pixel 7",       128, "Snow",     37999),
    ("Nothing", "Phone 2",       256, "White",    36999),
    ("Asus",    "ROG Phone 8",   256, "Phantom",  84999),
]

def build_simulated() -> pd.DataFrame:
    rows = []
    pid_map = {}
    for i, (br, mo, st, co, base_price) in enumerate(DEMO_PHONES):
        pid = f"SIM{i+1:03d}"
        pid_map[(br, mo, st)] = pid
        canonical_title = f"{br} {mo} {st}GB {co}"
        for j, seller in enumerate(random.sample(SELLERS, k=random.randint(2, 4))):
            price = round(base_price * random.uniform(0.96, 1.05) / 100) * 100
            rows.append({
                "source": "simulated",
                "seller": seller,
                "title": _messy(canonical_title, j),
                "brand": br,
                "price_inr": price,
                "stock": random.randint(1, 15),
                "storage_gb": st,
                "true_product_id": pid,
            })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════
#  MAIN BUILD
# ══════════════════════════════════════════════════════════════════════

def main():
    print("Loading sources…")
    gsm  = load_gsmarena()
    flip = load_flipkart()
    cell = load_cellphones()
    smart = load_smartphones_csv()
    sim  = build_simulated()

    # Assign ground truth to real data
    for df in [gsm, flip, cell, smart]:
        if "true_product_id" not in df.columns:
            df = assign_ground_truth(df)

    gsm  = assign_ground_truth(gsm)
    flip = assign_ground_truth(flip)
    cell = assign_ground_truth(cell)
    smart = assign_ground_truth(smart)

    # Combine — keep only listings with a real price > 1000 INR
    all_df = pd.concat([gsm, flip, cell, smart, sim], ignore_index=True)
    all_df = all_df[all_df["price_inr"] > 1000].copy()

    # listing_id
    all_df = all_df.reset_index(drop=True)
    all_df.insert(0, "listing_id", range(1, len(all_df) + 1))

    # Final columns
    cols = ["listing_id", "source", "seller", "title", "brand", "price_inr", "stock", "storage_gb", "true_product_id"]
    all_df = all_df[cols].fillna({"brand": "", "storage_gb": 0})
    all_df["storage_gb"] = all_df["storage_gb"].astype(int)

    out = ROOT / "listings.csv"
    all_df.to_csv(out, index=False)
    print(f"\n✅ listings.csv: {len(all_df)} rows  →  {out}")

    # Summary
    print("\n── Summary ──────────────────────────────")
    summary = all_df.groupby("source").agg(count=("listing_id","count")).reset_index()
    print(summary.to_string(index=False))
    n_real = all_df[all_df["source"] != "simulated"].shape[0]
    n_sim  = all_df[all_df["source"] == "simulated"].shape[0]
    n_prod = all_df["true_product_id"].nunique()
    print(f"\nReal: {n_real}  |  Simulated: {n_sim}  |  Unique true products: {n_prod}")

    matched = all_df[all_df["true_product_id"] != "UNMATCHED"]
    print(f"\n── Ground-truth pairs (true_product_id ≠ UNMATCHED): {len(matched)}")
    print(matched.groupby("true_product_id")[["seller","title","price_inr"]].head(2).to_string())

    # ── cart_data.json ─────────────────────────────────────────────────
    cart_products = [
        {"id": "cp1", "name": "Samsung Galaxy S24 256GB"},
        {"id": "cp2", "name": "Apple iPhone 15 128GB"},
        {"id": "cp3", "name": "OnePlus 12 256GB"},
        {"id": "cp4", "name": "Redmi Note 13 Pro 128GB"},
        {"id": "cp5", "name": "Samsung Galaxy A54 128GB"},
    ]
    cart_sellers = [
        {"id": "s1", "name": "QuickKart",  "shipping": 99},
        {"id": "s2", "name": "MegaMart",   "shipping": 49},
        {"id": "s3", "name": "ShopEase",   "shipping": 79},
        {"id": "s4", "name": "BazaarHub",  "shipping": 0},
    ]
    # prices[seller_id][product_id] — None if not stocked
    prices = {
        "s1": {"cp1": 68999, "cp2": 79999, "cp3": None,  "cp4": 24999, "cp5": 38999},
        "s2": {"cp1": 65499, "cp2": 77999, "cp3": 64999, "cp4": None,  "cp5": 37499},
        "s3": {"cp1": None,  "cp2": 81999, "cp3": 63999, "cp4": 23999, "cp5": None },
        "s4": {"cp1": 67999, "cp2": None,  "cp3": 65999, "cp4": 24499, "cp5": 39499},
    }
    cart_data = {"products": cart_products, "sellers": cart_sellers, "prices": prices}
    cart_path = ROOT / "cart_data.json"
    cart_path.write_text(json.dumps(cart_data, indent=2))
    print(f"\n✅ cart_data.json  →  {cart_path}")

    # ── flow_data.json ─────────────────────────────────────────────────
    flow_data = {
        "orders": [
            {"id": "o1", "product": "Samsung Galaxy S24",    "qty": 10, "buyer": "CityMobiles"},
            {"id": "o2", "product": "Apple iPhone 15",       "qty": 8,  "buyer": "TechZone"},
            {"id": "o3", "product": "OnePlus 12",            "qty": 6,  "buyer": "GadgetWorld"},
            {"id": "o4", "product": "Redmi Note 13 Pro",     "qty": 12, "buyer": "BudgetBuys"},
        ],
        "sellers": [
            {"id": "fs1", "name": "QuickKart",  "capacity": 15,
             "stocks": {"Samsung Galaxy S24": 8, "Apple iPhone 15": 5, "OnePlus 12": 0, "Redmi Note 13 Pro": 10}},
            {"id": "fs2", "name": "MegaMart",   "capacity": 20,
             "stocks": {"Samsung Galaxy S24": 6, "Apple iPhone 15": 7, "OnePlus 12": 8, "Redmi Note 13 Pro": 5}},
            {"id": "fs3", "name": "ShopEase",   "capacity": 10,
             "stocks": {"Samsung Galaxy S24": 0, "Apple iPhone 15": 4, "OnePlus 12": 6, "Redmi Note 13 Pro": 8}},
            {"id": "fs4", "name": "BazaarHub",  "capacity": 12,
             "stocks": {"Samsung Galaxy S24": 5, "Apple iPhone 15": 0, "OnePlus 12": 4, "Redmi Note 13 Pro": 7}},
        ]
    }
    flow_path = ROOT / "flow_data.json"
    flow_path.write_text(json.dumps(flow_data, indent=2))
    print(f"✅ flow_data.json  →  {flow_path}")


if __name__ == "__main__":
    main()
