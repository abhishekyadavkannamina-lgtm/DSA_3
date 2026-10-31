"""
algorithms/co4_max_flow.py
==========================
# ================================================
# CO USED: CO4 (Network Flow)
# TOPIC: Ford-Fulkerson with Edmonds-Karp (BFS) augmentation
# WHY IT IS HERE: Imagine sellers are water pipes and orders are water.
# Each pipe has a maximum capacity (seller stock limit).
# The SOURCE pushes water through the pipes toward the SINK.
# The SINK collects the water (fulfilled orders).
# Maximum water the network can carry = max orders fulfilled.
# Edmonds-Karp uses BFS so it always finds the shortest path,
# giving it a guaranteed polynomial time complexity of O(V · E²).
# ================================================
"""

from __future__ import annotations
from collections import deque
from typing import Optional


# ══════════════════════════════════════════════════════════════════════
#  GRAPH BUILDER
# ══════════════════════════════════════════════════════════════════════

def build_flow_graph(
    orders:  list[dict],
    sellers: list[dict],
) -> tuple[list[list[int]], dict[int, str], int, int, int]:
    """
    # CO USED: CO4 | WHY: Turn the real-world assignment problem into
    # a formal flow network with a source, order nodes, seller nodes, and a sink.

    Node layout:
        0               = SOURCE
        1 … n_orders    = one node per buyer order
        n+1 … n+m       = one node per seller
        n+m+1           = SINK

    Edges:
        Source  → Order_i    capacity = order quantity
        Order_i → Seller_j   capacity = min(order qty, seller stock)  if seller has product
        Seller_j → Sink       capacity = seller delivery capacity

    Returns
    -------
    (cap, labels, src_node, sink_node, n_nodes)
    cap    – adjacency matrix of capacities  (n_nodes × n_nodes)
    labels – node_index → human-readable label
    """
    n = len(orders)
    m = len(sellers)
    total = 1 + n + m + 1      # source + orders + sellers + sink
    src  = 0
    sink = total - 1

    cap    = [[0] * total for _ in range(total)]
    labels = {0: "SOURCE", sink: "SINK"}

    for i, order in enumerate(orders):
        o_node = i + 1
        labels[o_node] = f"Order: {order['product']}\n×{order['qty']}"
        # Source → order node: capacity = quantity demanded
        cap[src][o_node] = order["qty"]

        for j, seller in enumerate(sellers):
            s_node = n + 1 + j
            if i == 0:
                labels[s_node] = seller["name"]
            # Stock the seller has for this particular product
            stock = seller["stocks"].get(order["product"], 0)
            if stock > 0:
                # Capacity = min(what the buyer wants, what the seller has)
                cap[o_node][s_node] = min(order["qty"], stock)

    for j, seller in enumerate(sellers):
        s_node = n + 1 + j
        # Seller → sink: capacity = overall delivery capacity
        cap[s_node][sink] = seller["capacity"]

    return cap, labels, src, sink, total


# ══════════════════════════════════════════════════════════════════════
#  BFS (finds shortest augmenting path — the key to Edmonds-Karp)
# ══════════════════════════════════════════════════════════════════════

def _bfs(cap: list[list[int]], flow: list[list[int]],
         src: int, sink: int, n: int) -> Optional[list[int]]:
    """
    # CO USED: CO4 | WHY: BFS finds the shortest path from source to sink
    # in the RESIDUAL graph (where residual = capacity - current flow).
    # Edmonds-Karp's guarantee of polynomial time comes from always using BFS.

    Return a path from src to sink in the residual graph, or None if unreachable.
    """
    visited = [False] * n
    parent  = [-1] * n
    queue   = deque([src])
    visited[src] = True

    while queue:
        u = queue.popleft()
        for v in range(n):
            # Residual capacity must be > 0 to traverse this edge
            if not visited[v] and cap[u][v] - flow[u][v] > 0:
                visited[v]  = True
                parent[v]   = u
                if v == sink:
                    # Reconstruct path
                    path = []
                    cur  = sink
                    while cur != src:
                        path.append(cur)
                        cur = parent[cur]
                    path.append(src)
                    return path[::-1]
                queue.append(v)
    return None


# ══════════════════════════════════════════════════════════════════════
#  EDMONDS-KARP MAX FLOW
# ══════════════════════════════════════════════════════════════════════

def edmonds_karp(
    orders:  list[dict],
    sellers: list[dict],
) -> dict:
    """
    # CO USED: CO4 | WHY: This is the main max-flow algorithm.
    # Each iteration: find an augmenting path with BFS, push
    # as much flow as the bottleneck allows, update residual capacities.
    # Repeat until no augmenting path exists.

    Returns
    -------
    dict with:
        max_flow     – total units fulfilled
        total_demand – total units requested
        steps        – list of step dicts for the visualiser
        assignment   – which seller fulfils how many units of each order
        min_cut      – list of (u_label, v_label) cut edges
        node_labels  – dict index → label (for SVG rendering)
        n_nodes      – total node count
        src, sink    – source and sink node indices
    """
    cap, labels, src, sink, n_nodes = build_flow_graph(orders, sellers)

    # flow[u][v] = how much is currently flowing on edge u→v
    flow   = [[0] * n_nodes for _ in range(n_nodes)]
    # Make a mutable copy of cap for the residual graph
    res    = [row[:] for row in cap]

    steps: list[dict] = []
    total_flow = 0

    while True:
        path = _bfs(res, flow, src, sink, n_nodes)
        if path is None:
            break

        # Find the bottleneck (smallest residual capacity along the path)
        bottleneck = float("inf")
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            bottleneck = min(bottleneck, res[u][v] - flow[u][v])

        # Augment flow along the path
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            flow[u][v] += bottleneck
            flow[v][u] -= bottleneck   # update reverse edge (residual)

        total_flow += bottleneck

        steps.append({
            "path":        [labels.get(p, str(p)) for p in path],
            "path_nodes":  path,
            "bottleneck":  bottleneck,
            "total_flow":  total_flow,
        })

    # ── Build assignment summary ──────────────────────────────────────────
    n_orders = len(orders)
    assignment: list[dict] = []
    for j, seller in enumerate(sellers):
        s_node = n_orders + 1 + j
        for i, order in enumerate(orders):
            o_node = i + 1
            f = flow[o_node][s_node]
            if f > 0:
                assignment.append({
                    "seller":   seller["name"],
                    "order":    order["product"],
                    "buyer":    order.get("buyer", ""),
                    "qty":      f,
                })

    # ── Min-cut: find nodes reachable from source in residual ────────────
    visited = [False] * n_nodes
    queue   = deque([src])
    visited[src] = True
    while queue:
        u = queue.popleft()
        for v in range(n_nodes):
            if not visited[v] and res[u][v] - flow[u][v] > 0:
                visited[v] = True
                queue.append(v)

    min_cut_edges: list[dict] = []
    for u in range(n_nodes):
        for v in range(n_nodes):
            if visited[u] and not visited[v] and cap[u][v] > 0:
                min_cut_edges.append({
                    "from":     labels.get(u, str(u)),
                    "to":       labels.get(v, str(v)),
                    "capacity": cap[u][v],
                    "flow":     flow[u][v],
                })

    return {
        "max_flow":      total_flow,
        "total_demand":  sum(o["qty"] for o in orders),
        "steps":         steps,
        "assignment":    assignment,
        "min_cut":       min_cut_edges,
        "node_labels":   labels,
        "n_nodes":       n_nodes,
        "src":           src,
        "sink":          sink,
        "cap":           cap,
        "flow":          flow,
    }


# ══════════════════════════════════════════════════════════════════════
#  CONVENIENCE: find_min_cut (used directly by the route)
# ══════════════════════════════════════════════════════════════════════

def find_min_cut(result: dict) -> list[dict]:
    """Return the min-cut edges from an edmonds_karp result dict."""
    return result["min_cut"]
