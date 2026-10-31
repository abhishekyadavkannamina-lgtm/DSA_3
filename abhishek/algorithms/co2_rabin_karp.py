"""
algorithms/co2_rabin_karp.py
============================
# ================================================
# CO USED: CO2 (Linear-time string algorithms)
# TOPIC: Rabin-Karp with rolling hash
# WHY IT IS HERE: Product titles are just long strings.
# Instead of comparing every character of two titles,
# we convert each title into a number (a "hash").
# Two titles with the same hash are likely identical,
# so we only do the slow character check when the
# numbers match. This makes the whole process much
# faster — especially when scanning thousands of titles.
# ================================================
"""

from __future__ import annotations
from typing import Optional

# ── Constants ──────────────────────────────────────────────────────────────
BASE  = 31           # treat each character as a digit in base-31
MOD   = 1_000_000_007  # a large prime to keep the hash number small


# ── Core rolling hash ──────────────────────────────────────────────────────

def _char_value(c: str) -> int:
    """Map a character to a positive integer (a → 1, b → 2, …, space → 27, digit → itself)."""
    if c.isdigit():
        return int(c) + 27
    if c.isalpha():
        return ord(c.lower()) - ord('a') + 1
    return 27   # space and anything else


def rolling_hash(text: str, start: int, length: int,
                 base: int = BASE, mod: int = MOD) -> int:
    """
    # CO USED: CO2 | WHY: This is the core of Rabin-Karp.
    # We compute a number for a window of characters.
    Compute the polynomial rolling hash of text[start:start+length].
    h = c[0]*base^(n-1) + c[1]*base^(n-2) + … + c[n-1]  (mod p)
    """
    h = 0
    for i in range(length):
        h = (h * base + _char_value(text[start + i])) % mod
    return h


def compute_window_hashes(text: str, w: int,
                           base: int = BASE, mod: int = MOD) -> list[int]:
    """
    # CO USED: CO2 | WHY: Rolling update — we add the new character and
    # subtract the old one using a single multiply and mod.
    # This keeps each step O(1), making the whole scan O(n).

    Return a list of rolling hashes for every window of width w in text.
    Uses O(1) update per step.
    """
    n = text
    if len(text) < w:
        return []

    # Highest power: base^(w-1) mod p
    power = pow(base, w - 1, mod)

    hashes: list[int] = []
    h = rolling_hash(text, 0, w, base, mod)
    hashes.append(h)

    for i in range(1, len(text) - w + 1):
        # Remove the contribution of text[i-1] and add text[i+w-1]
        h = (h - _char_value(text[i - 1]) * power % mod + mod) % mod
        h = (h * base + _char_value(text[i + w - 1])) % mod
        hashes.append(h)

    return hashes


def rabin_karp_search(text: str, pattern: str,
                      base: int = BASE, mod: int = MOD
                      ) -> dict:
    """
    # CO USED: CO2 | WHY: We search for the pattern inside the text by
    # comparing hashes first and confirming only when hashes match.
    # This avoids comparing every character of the text for every position.

    Search for `pattern` inside `text` using Rabin-Karp.

    Returns
    -------
    dict with keys:
        positions   – list of start indices where pattern was found
        steps       – list of step dicts for the visualiser (window, hashes, result)
        collisions  – number of hash matches that turned out to be false (spurious hits)
    """
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return {"positions": [], "steps": [], "collisions": 0}

    pat_hash = rolling_hash(pattern, 0, m, base, mod)
    win_hashes = compute_window_hashes(text, m, base, mod)

    positions:  list[int]  = []
    steps:      list[dict] = []
    collisions: int        = 0

    for i, wh in enumerate(win_hashes):
        window = text[i: i + m]
        result = "no_match"

        if wh == pat_hash:
            if window == pattern:
                result = "match"
                positions.append(i)
            else:
                result = "collision"   # spurious hash match
                collisions += 1

        steps.append({
            "pos":        i,
            "window":     window,
            "win_hash":   wh,
            "pat_hash":   pat_hash,
            "result":     result,
        })

    return {"positions": positions, "steps": steps, "collisions": collisions}


# ── Full-title fingerprinting (used in matching pipeline) ──────────────────

def fingerprint_title(cleaned_title: str,
                      base: int = BASE, mod: int = MOD) -> int:
    """
    # CO USED: CO2 | WHY: Turn the entire cleaned title into a single
    # number so we can detect exact duplicate listings instantly.
    Compute the rolling hash of the full cleaned title.
    Two equal titles → identical fingerprints.
    """
    return rolling_hash(cleaned_title, 0, len(cleaned_title), base, mod)


def detect_exact_duplicates(titles: list[str]) -> dict[int, list[int]]:
    """
    Group titles that share the same fingerprint (and are truly equal).

    Returns a dict: hash_value → [list of indices with that hash].
    Only groups with more than one index are returned.
    """
    from collections import defaultdict
    buckets: dict[int, list[int]] = defaultdict(list)
    for i, t in enumerate(titles):
        h = fingerprint_title(t)
        buckets[h].append(i)

    # Keep only groups where more than one title has the same hash
    exact: dict[int, list[int]] = {}
    for h, idxs in buckets.items():
        if len(idxs) > 1:
            # Confirm: all must be string-equal (avoids keeping hash collisions)
            representative = titles[idxs[0]]
            true_dups = [i for i in idxs if titles[i] == representative]
            if len(true_dups) > 1:
                exact[h] = true_dups
    return exact
