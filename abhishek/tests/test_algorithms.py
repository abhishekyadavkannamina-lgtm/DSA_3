"""
tests/test_algorithms.py
========================
pytest test suite — all algorithm correctness tests.
Run:  pytest tests/test_algorithms.py -v
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest
from algorithms.cleaning       import clean_title, extract_details
from algorithms.co2_rabin_karp import rabin_karp_search, fingerprint_title, rolling_hash
from algorithms.co3_bitmask_dp import solve_bitmask_dp
from algorithms.co4_max_flow   import edmonds_karp
from algorithms.matching        import similarity_score, run_pipeline, UnionFind


# ══════════════════════════════════════════════════════════════════════
#  CO2 — Rabin-Karp
# ══════════════════════════════════════════════════════════════════════

class TestRabinKarp:

    def test_finds_all_positions(self):
        text    = "ababcabab"
        pattern = "abab"
        result  = rabin_karp_search(text, pattern)
        assert 0 in result["positions"]
        assert 5 in result["positions"]

    def test_no_match(self):
        result = rabin_karp_search("hello world", "xyz")
        assert result["positions"] == []

    def test_full_title_match(self):
        """Pattern == text → one match at position 0."""
        t = "samsung galaxy s24 256gb black"
        r = rabin_karp_search(t, t)
        assert r["positions"] == [0]

    def test_collision_count_is_int(self):
        r = rabin_karp_search("aaaaaa", "aa")
        assert isinstance(r["collisions"], int)

    def test_steps_length(self):
        """Steps should equal n - m + 1 when n >= m."""
        text, pat = "abcdef", "cd"
        r = rabin_karp_search(text, pat)
        assert len(r["steps"]) == len(text) - len(pat) + 1

    def test_rolling_hash_consistency(self):
        """Hash of same string must be the same every time."""
        h1 = rolling_hash("samsung", 0, 7)
        h2 = rolling_hash("samsung", 0, 7)
        assert h1 == h2

    def test_fingerprint_same_title(self):
        t = "apple iphone 15 128gb blue"
        assert fingerprint_title(t) == fingerprint_title(t)

    def test_fingerprint_different_title(self):
        assert fingerprint_title("apple iphone 15 128gb") != fingerprint_title("apple iphone 15 256gb")


# ══════════════════════════════════════════════════════════════════════
#  CO3 — Bitmask DP
# ══════════════════════════════════════════════════════════════════════

class TestBitmaskDP:

    def _simple_setup(self):
        products = ["p1", "p2"]
        sellers  = [
            {"id": "s1", "name": "Seller A", "shipping": 50},
            {"id": "s2", "name": "Seller B", "shipping": 100},
        ]
        prices = {
            "s1": {"p1": 300, "p2": None},   # s1 only has p1
            "s2": {"p1": None, "p2": 200},   # s2 only has p2
        }
        return products, sellers, prices

    def test_finds_optimal_when_forced_split(self):
        """Each seller stocks exactly one item — must buy from both."""
        products, sellers, prices = self._simple_setup()
        result = solve_bitmask_dp(products, sellers, prices)
        # Best cost = 300+50 + 200+100 = 650
        assert result["best_cost"] == 650.0

    def test_plan_is_nonempty(self):
        products, sellers, prices = self._simple_setup()
        result = solve_bitmask_dp(products, sellers, prices)
        assert len(result["plan"]) > 0

    def test_matches_brute_force(self):
        """DP answer must match brute-force exhaustive search for small n."""
        products = ["p1", "p2", "p3"]
        sellers  = [
            {"id": "s1", "name": "S1", "shipping": 50},
            {"id": "s2", "name": "S2", "shipping": 30},
        ]
        prices = {
            "s1": {"p1": 100, "p2": 150, "p3": 200},
            "s2": {"p1": 120, "p2": 100, "p3": 180},
        }

        dp_result = solve_bitmask_dp(products, sellers, prices)
        dp_cost   = dp_result["best_cost"]

        # Brute force: try all 2^3 = 8 assignments
        from itertools import product as iproduct
        from algorithms.co3_bitmask_dp import build_seller_subset_costs, INF
        n = len(products)
        sc = build_seller_subset_costs(products, sellers, prices)
        best_bf = INF
        for combo in iproduct(range(len(sellers)), repeat=n):
            # group by seller
            groups = {}
            for bit, si in enumerate(combo):
                groups.setdefault(si, []).append(bit)
            total = 0.0
            for si, bits in groups.items():
                mask = sum(1 << b for b in bits)
                c    = sc[sellers[si]["id"]][mask]
                if c >= INF:
                    total = INF; break
                total += c
            best_bf = min(best_bf, total)

        assert abs(dp_cost - best_bf) < 0.01

    def test_dp_table_length(self):
        products, sellers, prices = self._simple_setup()
        result = solve_bitmask_dp(products, sellers, prices)
        n = len(products)
        assert len(result["dp_table"]) == (1 << n) - 1


# ══════════════════════════════════════════════════════════════════════
#  CO4 — Edmonds-Karp Max Flow
# ══════════════════════════════════════════════════════════════════════

class TestEdmondsKarp:

    def _small_network(self):
        orders  = [{"product": "PhoneX", "qty": 5, "buyer": "B1"}]
        sellers = [
            {"id": "s1", "name": "S1", "capacity": 10,
             "stocks": {"PhoneX": 5}},
            {"id": "s2", "name": "S2", "capacity": 3,
             "stocks": {"PhoneX": 3}},
        ]
        return orders, sellers

    def test_max_flow_correct(self):
        orders, sellers = self._small_network()
        result = edmonds_karp(orders, sellers)
        # We want 5, s1 can supply all 5
        assert result["max_flow"] == 5

    def test_max_flow_does_not_exceed_demand(self):
        orders, sellers = self._small_network()
        result = edmonds_karp(orders, sellers)
        assert result["max_flow"] <= result["total_demand"]

    def test_known_example(self):
        """Classic example: two sellers can supply 5 + 3 = 8 units max."""
        orders  = [{"product": "PhoneX", "qty": 10, "buyer": "B1"}]  # wants 10
        sellers = [
            {"id": "s1", "name": "S1", "capacity": 5, "stocks": {"PhoneX": 5}},
            {"id": "s2", "name": "S2", "capacity": 3, "stocks": {"PhoneX": 3}},
        ]
        result = edmonds_karp(orders, sellers)
        assert result["max_flow"] == 8   # limited by seller capacities

    def test_steps_nonempty_when_flow_positive(self):
        orders, sellers = self._small_network()
        result = edmonds_karp(orders, sellers)
        if result["max_flow"] > 0:
            assert len(result["steps"]) > 0

    def test_min_cut_equals_max_flow(self):
        """Max-flow = sum of capacities across min-cut edges."""
        orders, sellers = self._small_network()
        result = edmonds_karp(orders, sellers)
        cut_cap = sum(e["flow"] for e in result["min_cut"])
        assert cut_cap == result["max_flow"]


# ══════════════════════════════════════════════════════════════════════
#  Matching pipeline tests
# ══════════════════════════════════════════════════════════════════════

class TestMatching:

    def test_samsung_s24_group_together(self):
        """The two Samsung S24 demo listings must be in the same group."""
        listings = [
            {"listing_id": 1, "title": "Samsung Galaxy S24 256GB Black",
             "seller": "QuickKart", "price_inr": 68999},
            {"listing_id": 2, "title": "Samsung S24 - 256 GB - Black",
             "seller": "MegaMart",  "price_inr": 65499},
        ]
        result = run_pipeline(listings, threshold=0.75)
        # There should be exactly 1 group
        assert len(result["groups"]) == 1

    def test_iphone_storage_sizes_stay_separate(self):
        """iPhone 15 128GB and iPhone 15 256GB must NOT be merged."""
        listings = [
            {"listing_id": 1, "title": "Apple iPhone 15 128GB Blue",
             "seller": "QuickKart", "price_inr": 79999},
            {"listing_id": 2, "title": "Apple iPhone 15 256GB Blue",
             "seller": "MegaMart",  "price_inr": 89999},
        ]
        result = run_pipeline(listings, threshold=0.80)
        assert len(result["groups"]) == 2, "Different storage → different groups"

    def test_s24_vs_s24_ultra_stay_separate(self):
        """Samsung Galaxy S24 and Galaxy S24 Ultra must NOT merge."""
        listings = [
            {"listing_id": 1, "title": "Samsung Galaxy S24 256GB Black",
             "seller": "A", "price_inr": 68999},
            {"listing_id": 2, "title": "Samsung Galaxy S24 Ultra 256GB Black",
             "seller": "B", "price_inr": 124999},
        ]
        result = run_pipeline(listings, threshold=0.80)
        assert len(result["groups"]) == 2, "S24 vs S24 Ultra → different groups"

    def test_best_price_correct(self):
        """Best price in a group should be the minimum."""
        listings = [
            {"listing_id": 1, "title": "Samsung Galaxy S24 256GB Black",
             "seller": "QuickKart", "price_inr": 68999},
            {"listing_id": 2, "title": "Samsung S24 - 256 GB - Black",
             "seller": "MegaMart",  "price_inr": 65499},
        ]
        result = run_pipeline(listings, threshold=0.75)
        group = list(result["groups"].values())[0]
        assert group["best_price"] == 65499

    def test_union_find_basic(self):
        uf = UnionFind(5)
        uf.union(0, 1)
        uf.union(1, 2)
        assert uf.find(0) == uf.find(2)
        assert uf.find(3) != uf.find(0)

    def test_similarity_exact_same(self):
        t = "apple iphone 15 128gb blue"
        assert similarity_score(t, t) == 1.0

    def test_similarity_storage_mismatch_low(self):
        """Listings differing only in storage must score below 0.80."""
        s = similarity_score("apple iphone 15 128gb blue", "apple iphone 15 256gb blue")
        assert s < 0.80, f"Expected <0.80, got {s}"

    def test_cleaning_normalises(self):
        raw = "Samsung S24 - 256 GB - Black"
        c   = clean_title(raw)
        assert "256gb" in c
        assert "-" not in c
        assert c == c.lower()
