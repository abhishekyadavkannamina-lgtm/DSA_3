"""
algorithms/matching.py
======================
Combines Rabin-Karp fingerprinting (exact duplicates) with
RapidFuzz fuzzy scoring (near-matches) and Union-Find grouping
to produce canonical product groups from a list of raw listings.
"""

from __future__ import annotations
from typing import Optional
import re

from rapidfuzz import fuzz

from .cleaning import clean_title, extract_details
from .co2_rabin_karp import fingerprint_title


# ══════════════════════════════════════════════════════════════════════
#  UNION-FIND (Disjoint Set Union)
#  Efficiently groups listings that belong to the same product.
# ══════════════════════════════════════════════════════════════════════

class UnionFind:
    """
    Union-Find (Disjoint Set Union) with path compression and union by rank.

    WHY: After we decide that listing A and listing B are the same product,
    we need to efficiently "merge" them into one group. Union-Find does
    this in nearly O(1) amortised time per operation.
    """

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank   = [0] * n

    def find(self, x: int) -> int:
        """Return the root of x's group, compressing the path as we go."""
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        """Merge the groups of x and y."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def groups(self) -> dict[int, list[int]]:
        """Return {root: [member indices ...]} for all groups."""
        from collections import defaultdict
        d: dict[int, list[int]] = defaultdict(list)
        for i in range(len(self.parent)):
            d[self.find(i)].append(i)
        return dict(d)


# ══════════════════════════════════════════════════════════════════════
#  SIMILARITY SCORE
# ══════════════════════════════════════════════════════════════════════

def _detail_penalty(da: dict, db: dict) -> float:
    """
    Return a penalty (0.0 – 0.5) based on mismatched key details.

    A storage mismatch is a hard near-miss flag (high penalty).
    A brand or colour mismatch gets a smaller penalty.
    """
    penalty = 0.0

    # Storage mismatch is a strong signal they are DIFFERENT products
    sa, sb = da.get("storage"), db.get("storage")
    if sa and sb and sa != sb:
        penalty += 0.45   # almost certainly different SKUs

    # Brand mismatch
    ba, bb = da.get("brand"), db.get("brand")
    if ba and bb and ba != bb:
        penalty += 0.40

    # Colour mismatch is a smaller penalty (same product, different colour)
    ca, cb = da.get("colour"), db.get("colour")
    if ca and cb and ca != cb:
        penalty += 0.05

    return penalty


def _model_variant_penalty(cleaned_a: str, cleaned_b: str) -> float:
    """
    Extra penalty when one title has a distinguishing variant word that the other lacks.
    e.g. 'ultra', 'pro', 'plus', 'max', 'fe', 'lite', 'mini'
    """
    VARIANTS = {"ultra", "pro", "plus", "max", "fe", "lite", "mini", "edge", "fold", "flip"}
    tokens_a = set(cleaned_a.split())
    tokens_b = set(cleaned_b.split())
    only_in_a = tokens_a & VARIANTS - tokens_b
    only_in_b = tokens_b & VARIANTS - tokens_a
    if only_in_a or only_in_b:
        return 0.35   # strong: one has 'ultra', other doesn't → different product
    return 0.0


def similarity_score(title_a: str, title_b: str,
                     details_a: Optional[dict] = None,
                     details_b: Optional[dict] = None) -> float:
    """
    Compute a 0–1 similarity score between two cleaned titles.

    Uses:
    - Rabin-Karp fingerprint (exact match → 1.0)
    - RapidFuzz token_set_ratio for fuzzy similarity
    - Detail penalty for storage/brand/colour mismatches

    Returns a float between 0.0 and 1.0.
    """
    # Exact hash match
    if fingerprint_title(title_a) == fingerprint_title(title_b) and title_a == title_b:
        return 1.0

    # Fuzzy token score (0-100 → 0-1)
    fuzzy = fuzz.token_set_ratio(title_a, title_b) / 100.0

    # Apply penalty for key-detail mismatches
    if details_a is None:
        details_a = extract_details(title_a)
    if details_b is None:
        details_b = extract_details(title_b)

    penalty = _detail_penalty(details_a, details_b)
    penalty += _model_variant_penalty(title_a, title_b)
    score = max(0.0, fuzzy - penalty)
    return round(score, 4)


# ══════════════════════════════════════════════════════════════════════
#  PIPELINE: CLEAN → SCORE → GROUP
# ══════════════════════════════════════════════════════════════════════

def run_pipeline(listings: list[dict], threshold: float = 0.80) -> dict:
    """
    Full matching pipeline.

    Parameters
    ----------
    listings   : list of dicts with at least 'listing_id', 'title', 'seller', 'price_inr'
    threshold  : minimum similarity to merge two listings into the same product

    Returns
    -------
    dict with:
        cleaned_listings  – each listing with a 'cleaned' title and extracted details
        pairs             – every compared pair with their score
        groups            – {group_id: [listing dicts]} canonical product groups
    """
    n = len(listings)

    # Step 1: Clean every title and extract details
    cleaned = []
    for row in listings:
        c = clean_title(row["title"])
        d = extract_details(c)
        cleaned.append({**row, "cleaned": c, "details": d})

    # Step 2: Score every unique pair (O(n²) — fine for n ≤ 200)
    pairs: list[dict] = []
    uf = UnionFind(n)

    for i in range(n):
        for j in range(i + 1, n):
            score = similarity_score(
                cleaned[i]["cleaned"], cleaned[j]["cleaned"],
                cleaned[i]["details"], cleaned[j]["details"],
            )
            pairs.append({
                "i": i, "j": j,
                "title_a": listings[i]["title"],
                "title_b": listings[j]["title"],
                "score": score,
                "merged": score >= threshold,
            })
            if score >= threshold:
                uf.union(i, j)

    # Step 3: Build canonical groups
    raw_groups = uf.groups()
    groups: dict[str, list[dict]] = {}
    for root, members in sorted(raw_groups.items()):
        gid = f"G{root:03d}"
        member_rows = [cleaned[m] for m in members]
        # Canonical name = longest cleaned title in the group (most specific)
        canonical = max(member_rows, key=lambda r: len(r["cleaned"]))["title"]
        groups[gid] = {
            "canonical": canonical,
            "listings": member_rows,
            "best_price": min(r["price_inr"] for r in member_rows),
            "best_seller": min(member_rows, key=lambda r: r["price_inr"])["seller"],
        }

    return {
        "cleaned_listings": cleaned,
        "pairs": pairs,
        "groups": groups,
    }
