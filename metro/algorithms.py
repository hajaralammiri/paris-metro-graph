"""Graph algorithms written from scratch (no networkx), tested against networkx.

- dijkstra:            single-source shortest paths with a binary heap, O((V+E) log V)
- shortest_path:       multi-source / multi-target route between two stations
- pagerank:            power iteration on the transition matrix
- betweenness:         Brandes' algorithm for weighted graphs, O(V E + V^2 log V)
"""

from __future__ import annotations

import heapq
from collections import defaultdict
from typing import Hashable, Iterable

Graph = dict[Hashable, dict[Hashable, float]]


def dijkstra(graph: Graph, sources: Iterable[Hashable]):
    """Shortest distances from a *set* of sources (all start at distance 0).

    Returns (dist, parent) where parent[v] is the previous node on a
    shortest path to v. Starting from several sources lets us route from
    a station regardless of which platform (line/direction) we board.
    """
    dist: dict = {}
    parent: dict = {}
    heap = []
    for s in sources:
        dist[s] = 0.0
        parent[s] = None
        heap.append((0.0, id(s), s))
    heapq.heapify(heap)
    done = set()
    while heap:
        d, _, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        for v, w in graph.get(u, {}).items():
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                parent[v] = u
                heapq.heappush(heap, (nd, id(v), v))
    return dist, parent


def shortest_path(graph: Graph, sources, targets):
    """Fastest path from any node in `sources` to any node in `targets`."""
    targets = set(targets)
    dist, parent = dijkstra(graph, sources)
    reachable = [t for t in targets if t in dist]
    if not reachable:
        return float("inf"), []
    end = min(reachable, key=dist.__getitem__)
    path = [end]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    return dist[end], path[::-1]


def pagerank(graph: Graph, damping: float = 0.85, tol: float = 1e-10, max_iter: int = 200):
    """PageRank by power iteration.

    r_{k+1}(v) = (1-d)/N + d * sum_{u -> v} r_k(u) / outdeg(u)
    Dangling nodes (no out-edges) spread their rank uniformly.
    """
    nodes = list(graph)
    n = len(nodes)
    rank = {v: 1.0 / n for v in nodes}
    for _ in range(max_iter):
        dangling = sum(rank[u] for u in nodes if not graph[u])
        new = {v: (1 - damping) / n + damping * dangling / n for v in nodes}
        for u in nodes:
            out = graph[u]
            if out:
                share = damping * rank[u] / len(out)
                for v in out:
                    new[v] += share
        if sum(abs(new[v] - rank[v]) for v in nodes) < tol:
            return new
        rank = new
    return rank


def betweenness(graph: Graph, normalized: bool = True):
    """Brandes' betweenness centrality on a weighted graph.

    A station has high betweenness if many fastest routes pass through it.
    """
    bc = dict.fromkeys(graph, 0.0)
    for s in graph:
        # 1) Dijkstra from s, counting shortest paths (sigma) and predecessors
        stack: list = []
        preds: dict = defaultdict(list)
        sigma = dict.fromkeys(graph, 0.0)
        sigma[s] = 1.0
        best = {s: 0.0}          # tentative distances
        final: set = set()       # settled nodes
        heap = [(0.0, id(s), s)]
        while heap:
            d, _, v = heapq.heappop(heap)
            if v in final or d > best[v]:
                continue
            final.add(v)
            stack.append(v)
            for w, wt in graph[v].items():
                if w in final:
                    continue
                nd = d + wt
                if nd < best.get(w, float("inf")):
                    best[w] = nd
                    sigma[w] = sigma[v]
                    preds[w] = [v]
                    heapq.heappush(heap, (nd, id(w), w))
                elif nd == best[w]:
                    sigma[w] += sigma[v]
                    preds[w].append(v)
        # accumulation
        delta = dict.fromkeys(graph, 0.0)
        while stack:
            w = stack.pop()
            for v in preds[w]:
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]
    n = len(graph)
    # undirected graph: every path counted twice
    for v in bc:
        bc[v] /= 2
        if normalized and n > 2:
            bc[v] /= (n - 1) * (n - 2) / 2
    return bc
