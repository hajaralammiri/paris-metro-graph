"""Check the from-scratch algorithms against networkx."""

import math
import random

import networkx as nx
import pytest

from metro.algorithms import betweenness, dijkstra, pagerank, shortest_path
from metro.network import MetroNetwork, normalize


def random_graph(n=40, p=0.12, seed=0, undirected=False):
    rng = random.Random(seed)
    g = {i: {} for i in range(n)}
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < p:
                w = rng.randint(1, 20)
                g[u][v] = w
                if undirected:
                    g[v][u] = w
    return g


def to_nx(g, directed=True):
    G = nx.DiGraph() if directed else nx.Graph()
    G.add_nodes_from(g)
    for u, nbrs in g.items():
        for v, w in nbrs.items():
            G.add_edge(u, v, weight=w)
    return G


@pytest.mark.parametrize("seed", range(5))
def test_dijkstra_matches_networkx(seed):
    g = random_graph(seed=seed)
    dist, _ = dijkstra(g, [0])
    expected = nx.single_source_dijkstra_path_length(to_nx(g), 0)
    assert dist == pytest.approx(expected)


def test_shortest_path_is_consistent():
    g = random_graph(seed=1)
    d, path = shortest_path(g, [0], [7])
    assert path[0] == 0 and path[-1] == 7
    assert d == pytest.approx(sum(g[a][b] for a, b in zip(path, path[1:])))


@pytest.mark.parametrize("seed", range(3))
def test_pagerank_matches_networkx(seed):
    g = random_graph(seed=seed)
    ours = pagerank(g)
    theirs = nx.pagerank(to_nx(g), alpha=0.85, weight=None, tol=1e-12)
    for v in g:
        assert ours[v] == pytest.approx(theirs[v], abs=1e-6)


@pytest.mark.parametrize("seed", range(3))
def test_betweenness_matches_networkx(seed):
    g = random_graph(n=30, p=0.15, seed=seed, undirected=True)
    ours = betweenness(g)
    theirs = nx.betweenness_centrality(to_nx(g, directed=False), weight="weight")
    for v in g:
        assert ours[v] == pytest.approx(theirs[v], abs=1e-9)


def test_normalize():
    assert normalize("Châtelet") == normalize("chatelet")


def test_real_network_route():
    net = MetroNetwork.from_csv()
    a, b = net.find_station("Chatelet"), net.find_station("Nation")
    seconds, path = shortest_path(net.adj, net.platforms_of(a), net.platforms_of(b))
    assert path and math.isfinite(seconds)
    assert 5 * 60 < seconds < 40 * 60
