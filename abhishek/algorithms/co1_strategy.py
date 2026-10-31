"""
algorithms/co1_strategy.py
==========================
# ================================================
# CO USED: CO1 (Problem-class signatures and strategy selection)
# TOPIC: Evaluating a problem's "signature" to choose the right algorithm
# WHY IT IS HERE: Before writing any code, a good engineer asks:
# "What kind of problem IS this?" — Is it a search problem?
# A counting problem? An optimisation over subsets? A flow problem?
# Each type has a known-best algorithm. This module acts like
# a decision tree: read the keywords, match the signature,
# recommend the right algorithm. Like a doctor reading symptoms
# and prescribing a treatment.
# ================================================
"""

from __future__ import annotations


# ── Strategy definitions ───────────────────────────────────────────────────

STRATEGIES = [
    {
        "id":         "rabin_karp",
        "co":         "CO2",
        "signature":  "string search / text matching / duplicate detection",
        "strategy":   "Rabin-Karp Rolling Hash",
        "reason":     (
            "The problem is about comparing or searching inside text strings. "
            "Rabin-Karp converts each string into a number (a hash) so "
            "comparison is instant instead of character-by-character."
        ),
        "complexity": "O(n + m)  — linear time",
        "page":       "/match",
        "keywords":   ["same", "match", "similar", "duplicate", "title", "string",
                       "text", "search", "substring", "listing", "product name",
                       "fingerprint", "hash"],
    },
    {
        "id":         "bitmask_dp",
        "co":         "CO3",
        "signature":  "combinatorial optimisation over subsets / cheapest combination",
        "strategy":   "Bitmask Dynamic Programming",
        "reason":     (
            "The problem asks for the best (cheapest) way to split a shopping "
            "cart across sellers. With n products there are 2ⁿ possible subsets. "
            "Bitmask DP stores the best answer for every subset, so we never "
            "redo the same calculation — much faster than trying every combination."
        ),
        "complexity": "O(n · 3ⁿ)  — exponential but small n (≤ 5)",
        "page":       "/cart",
        "keywords":   ["cheapest", "minimum cost", "cart", "buy", "seller",
                       "combination", "shipping", "subset", "total price",
                       "split", "optimal", "cheapest way"],
    },
    {
        "id":         "edmonds_karp",
        "co":         "CO4",
        "signature":  "capacity-constrained assignment / flow on a network",
        "strategy":   "Edmonds-Karp Max-Flow",
        "reason":     (
            "The problem has sellers with limited stock and orders that "
            "need to be fulfilled. This is exactly a 'flow through a pipe' "
            "problem — orders flow from a source through sellers to a sink. "
            "Edmonds-Karp finds the maximum number of orders that can be "
            "filled without exceeding any seller's stock limit."
        ),
        "complexity": "O(V · E²)  — polynomial",
        "page":       "/assign",
        "keywords":   ["assign", "stock", "capacity", "limited", "fulfil",
                       "allocate", "flow", "order", "dispatch", "ship",
                       "maximum orders", "network"],
    },
    {
        "id":         "brute_force_trap",
        "co":         "CO1 (what NOT to do)",
        "signature":  "brute force / try every combination",
        "strategy":   "Brute Force — ❌ Avoid This!",
        "reason":     (
            "Trying every seller combination one by one takes 4ⁿ steps "
            "(with 4 sellers and 5 items that is already 1,024 combinations). "
            "With 10 items it explodes to over 1 million. "
            "Bitmask DP solves the same problem in n · 2ⁿ = 50 steps for n=5 — "
            "20× faster, and the gap grows exponentially."
        ),
        "complexity": "O(4ⁿ)  — exponential, impractical",
        "page":       None,
        "keywords":   ["brute", "every combination", "try all", "exhaustive",
                       "naive", "loop through all"],
    },
]


def classify_problem(description: str) -> dict:
    """
    # CO USED: CO1 | WHY: Read a plain-English problem description,
    # count keyword hits, and return the best-matching strategy.

    Parameters
    ----------
    description : str
        A plain-English description of the problem the user wants to solve.

    Returns
    -------
    dict  — the best-matching strategy entry from STRATEGIES, or the brute-force
            trap if nothing matches.
    """
    desc_lower = description.lower()

    best_match  = None
    best_hits   = 0

    for strat in STRATEGIES:
        hits = sum(1 for kw in strat["keywords"] if kw in desc_lower)
        if hits > best_hits:
            best_hits  = hits
            best_match = strat

    if best_match is None or best_hits == 0:
        # Default: return a "not sure" message
        return {
            "id":         "unknown",
            "co":         "—",
            "signature":  "unclear",
            "strategy":   "Could not classify",
            "reason":     "Try describing the problem with more detail.",
            "complexity": "—",
            "page":       None,
        }

    return best_match


# ── Growth comparison table (brute force vs DP) ───────────────────────────

def growth_table() -> list[dict]:
    """
    # CO USED: CO1 | WHY: Shows concretely WHY brute force is bad and DP is better.

    Return rows comparing brute-force growth (4ⁿ) vs bitmask DP (n · 2ⁿ)
    for n = 5, 10, 15, 20.
    """
    rows = []
    for n in [5, 10, 15, 20]:
        bf  = 4 ** n
        dp  = n * (2 ** n)
        rows.append({
            "n":          n,
            "brute_force": bf,
            "dp_bitmask":  dp,
            "speedup":     round(bf / dp) if dp else "∞",
        })
    return rows
