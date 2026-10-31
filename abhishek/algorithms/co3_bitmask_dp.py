"""
algorithms/co3_bitmask_dp.py
=============================
# ================================================
# CO USED: CO3 (Advanced Dynamic Programming)
# TOPIC: Bitmask DP — finding the cheapest shopping cart
# WHY IT IS HERE: A shopper wants to buy n products.
# Each of 4 sellers sells some products at different prices,
# and each seller charges ONE shipping fee if you buy from them.
# The cheapest total is NOT simply buying each item from whoever
# sells it cheapest (because you might pay 4 shipping fees).
# We need to decide which SUBSET of items to buy from each seller.
# With n=5 items there are 2^5 = 32 possible subsets per seller.
# Bitmask DP stores the cheapest way to cover every possible
# combination of products. It reuses earlier answers so we
# never repeat the same calculation. Much faster than brute force.
# ================================================
"""

from __future__ import annotations
from typing import Optional

INF = float("inf")


# ── Pre-compute how much each seller costs for each subset ─────────────────

def build_seller_subset_costs(
    products:  list[str],
    sellers:   list[dict],
    prices:    dict[str, dict[str, Optional[float]]],
) -> dict[str, list[float]]:
    """
    # CO USED: CO3 | WHY: For every seller and every subset of products,
    # we pre-compute the total cost (items + shipping).
    # seller_subset_cost[seller_id][mask] = total cost, or INF if the
    # seller doesn't stock every item in the subset.

    Parameters
    ----------
    products : list of product IDs in a fixed order (determines bit positions)
    sellers  : list of dicts with 'id', 'name', 'shipping'
    prices   : prices[seller_id][product_id] = price (None if not stocked)

    Returns
    -------
    dict seller_id → list of floats indexed by bitmask (length 2^n)
    """
    n = len(products)
    full = 1 << n   # = 2^n

    costs: dict[str, list[float]] = {}

    for s in sellers:
        sid = s["id"]
        shipping = s.get("shipping", 0)
        seller_prices = prices.get(sid, {})
        c: list[float] = [0.0] * full

        for mask in range(full):
            if mask == 0:
                c[0] = 0.0
                continue
            # Check every bit that is set in mask
            total = 0.0
            valid = True
            for bit in range(n):
                if mask & (1 << bit):
                    pid   = products[bit]
                    price_obj = seller_prices.get(pid)
                    if price_obj is None:   # seller doesn't stock this product
                        valid = False
                        break
                    # Extract the total cost if it's a dict, otherwise fallback to float
                    total += price_obj["total"] if isinstance(price_obj, dict) else price_obj
            if valid:
                c[mask] = total + shipping  # add shipping once per seller
            else:
                c[mask] = INF

        costs[sid] = c

    return costs


def solve_bitmask_dp(
    products: list[str],
    sellers:  list[dict],
    prices:   dict[str, dict[str, Optional[float]]],
) -> dict:
    """
    # CO USED: CO3 | WHY: This is the heart of the Bitmask DP.
    # dp[mask] = minimum cost to buy exactly the products whose bits are 1 in mask.
    # We build up from mask=0 (nothing bought) to mask=111…1 (all bought).
    # For each mask we try every seller and every non-empty submask.

    Returns
    -------
    dict with:
        best_cost    – minimum total cost to buy all products
        plan         – list of {seller, product_ids, cost} assignments
        dp_table     – list of {mask_bin, products_in_mask, cost, from_seller, from_sub}
                       for the step-by-step visualiser
        comparison   – single_seller_best, greedy_item_cost, dp_cost and savings
    """
    n    = len(products)
    full = (1 << n) - 1   # all products bought mask

    subset_costs = build_seller_subset_costs(products, sellers, prices)

    # ── DP ────────────────────────────────────────────────────────────────
    dp:          list[float]         = [INF] * (full + 1)
    parent_sub:  list[Optional[int]] = [None] * (full + 1)  # which submask was chosen
    parent_sell: list[Optional[str]] = [None] * (full + 1)  # which seller was chosen

    dp[0] = 0.0

    # Enumerate all masks in ascending order
    dp_table: list[dict] = []

    for mask in range(1, full + 1):
        # Try every non-empty submask of mask for every seller
        sub = mask
        while sub > 0:
            for s in sellers:
                sid  = s["id"]
                cost = subset_costs[sid][sub]
                if cost < INF:
                    remaining = mask ^ sub   # bits not covered by this seller
                    if dp[remaining] < INF:
                        candidate = dp[remaining] + cost
                        if candidate < dp[mask]:
                            dp[mask]          = candidate
                            parent_sub[mask]  = sub
                            parent_sell[mask] = sid
            sub = (sub - 1) & mask  # enumerate next submask

        # Record for visualiser
        products_in = [products[b] for b in range(n) if mask & (1 << b)]
        mask_bin    = format(mask, f"0{n}b")
        dp_table.append({
            "mask":             mask,
            "mask_bin":         mask_bin,
            "products_in_mask": products_in,
            "cost":             dp[mask] if dp[mask] < INF else None,
            "from_seller":      parent_sell[mask],
            "from_sub":         format(parent_sub[mask], f"0{n}b") if parent_sub[mask] else None,
        })

    # ── Reconstruct plan ─────────────────────────────────────────────────
    plan: list[dict] = []
    cur = full
    while cur > 0 and parent_sub[cur] is not None:
        sub  = parent_sub[cur]
        sid  = parent_sell[cur]
        items = [products[b] for b in range(n) if sub & (1 << b)]
        s_obj = next(s for s in sellers if s["id"] == sid)
        plan.append({
            "seller":    s_obj.get("name", sid),
            "seller_id": sid,
            "items":     items,
            "cost":      subset_costs[sid][sub],
        })
        cur = cur ^ sub

    # ── Comparison numbers ─────────────────────────────────────────────
    # Best single-seller (buys everything from one seller)
    single_best = INF
    for s in sellers:
        c = subset_costs[s["id"]][full]
        if c < single_best:
            single_best = c

    # Greedy: cheapest per-item ignoring shipping
    greedy = 0.0
    for pid in products:
        item_prices = []
        for s in sellers:
            price_obj = prices[s["id"]].get(pid)
            if price_obj is not None:
                item_prices.append(price_obj["total"] if isinstance(price_obj, dict) else price_obj)
        if item_prices:
            greedy += min(item_prices)
        else:
            greedy = INF

    best = dp[full]

    return {
        "best_cost":   best if best < INF else None,
        "plan":        plan,
        "dp_table":    dp_table,
        "comparison": {
            "dp_cost":            best if best < INF else None,
            "single_seller_best": single_best if single_best < INF else None,
            "greedy_item_cost":   greedy if greedy < INF else None,
            "savings_vs_single":  round(single_best - best) if best < INF and single_best < INF else None,
        },
    }
