"""
algorithms/cleaning.py
======================
Cleans and standardises messy e-commerce product titles so that
"Samsung S24 - 256 GB - Black" and "Samsung Galaxy S24 256GB Black"
become close enough to compare properly.

This is the preparation step before any matching or hashing.
"""

import re
from typing import Optional


# Words that add no useful product info and should be removed
FILLER_WORDS = {
    "new", "sealed", "unlocked", "smartphone", "phone", "mobile",
    "buy", "best", "deal", "offer", "official", "original", "genuine",
    "india", "version", "edition", "latest", "model", "refurbished", "open",
}

# Expand storage shorthand written in different ways
STORAGE_PATTERNS = [
    (re.compile(r"(\d+)\s*tb", re.I), r"\1tb"),
    (re.compile(r"(\d+)\s*gb", re.I), r"\1gb"),
    (re.compile(r"(\d+)\s*mb", re.I), r"\1mb"),
]

# Known brand names — used to detect and normalise brand in title
KNOWN_BRANDS = [
    "apple", "samsung", "oneplus", "redmi", "xiaomi", "realme",
    "poco", "motorola", "moto", "oppo", "vivo", "nokia", "asus",
    "google", "sony", "lg", "huawei", "honor",
]


def clean_title(raw: str) -> str:
    """
    Return a normalised, lowercase version of a product title.

    Steps:
        1. Lowercase everything.
        2. Join 'number UNIT' → 'numberunit'   e.g. '256 GB' → '256gb'
        3. Remove all punctuation and extra symbols.
        4. Strip common filler words.
        5. Collapse multiple spaces into one.

    Parameters
    ----------
    raw : str  The original, messy product title.

    Returns
    -------
    str  Cleaned title, ready for hashing or similarity scoring.
    """
    t = str(raw).lower().strip()

    # Step 2 — join number + unit
    for pattern, replacement in STORAGE_PATTERNS:
        t = pattern.sub(replacement, t)

    # Step 3 — remove brackets, dashes, slashes, commas …
    t = re.sub(r"[^a-z0-9\s]", " ", t)

    # Step 4 — remove filler words
    tokens = t.split()
    tokens = [tok for tok in tokens if tok not in FILLER_WORDS]

    # Step 5 — collapse spaces
    return " ".join(tokens).strip()


def extract_details(cleaned: str) -> dict:
    """
    Pull out brand, storage size, RAM and colour from a cleaned title.

    Returns a dict with keys: brand, storage, ram, colour.
    Any undetected field is None.
    """
    brand   = _extract_brand(cleaned)
    storage = _extract_storage(cleaned)
    ram     = _extract_ram(cleaned)
    colour  = _extract_colour(cleaned)
    return {"brand": brand, "storage": storage, "ram": ram, "colour": colour}


def _extract_brand(t: str) -> Optional[str]:
    for b in KNOWN_BRANDS:
        if b in t.split():
            return b
    return None


def _extract_storage(t: str) -> Optional[int]:
    """Return the storage in GB (int) or None."""
    m = re.search(r"(\d+)gb", t)
    if m:
        val = int(m.group(1))
        # Sanity: typical phone storage is between 4 and 2048 GB
        if 4 <= val <= 2048:
            return val
    return None


def _extract_ram(t: str) -> Optional[int]:
    """Return the RAM in GB (int) or None.  We look for the SMALLER number before 'gb'."""
    matches = [int(m.group(1)) for m in re.finditer(r"(\d+)gb", t)]
    if len(matches) >= 2:
        return min(matches)   # smaller one is usually RAM
    return None


# Basic colour vocabulary
_COLOURS = {
    "black", "white", "blue", "red", "green", "silver", "gold",
    "yellow", "purple", "pink", "grey", "gray", "orange", "violet",
}

def _extract_colour(t: str) -> Optional[str]:
    for word in t.split():
        if word in _COLOURS:
            return word
    return None
