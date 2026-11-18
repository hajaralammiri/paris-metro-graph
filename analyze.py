"""Network analysis of the Paris Metro: key stations and extreme journeys.

Usage:
    python analyze.py
Writes figures to figures/.
"""

from pathlib import Path

import matplotlib.pyplot as plt

from metro.algorithms import betweenness, dijkstra, pagerank
from metro.network import MetroNetwork

FIG = Path(__file__).resolve().parent / "figures"


def top(scores: dict, k: int = 10):
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]


def bar_chart(items, title, xlabel, path):
    names = [n for n, _ in items][::-1]
    values = [v for _, v in items][::-1]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(names, values, color="#2f5d8a")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    FIG.mkdir(exist_ok=True)
    net = MetroNetwork.from_csv()
    g = net.station_graph()
    print(net)

    # 1) Degree: how many direct neighbours a station has
    degree = {s: len(n) for s, n in g.items()}
    print("\nMost connected stations (degree):")
    for s, d in top(degree, 5):
        print(f"  {s:30s} {d}")

    # 2) Betweenness: how many fastest routes go through a station
    bc = betweenness(g)
    print("\nBetweenness centrality (share of fastest routes passing through):")
    for s, v in top(bc):
        print(f"  {s:30s} {v:.3f}")
    bar_chart(top(bc), "Paris Metro: betweenness centrality", "share of fastest routes", FIG / "betweenness.png")

    # 3) PageRank on the station graph
    pr = pagerank(g)
    print("\nPageRank:")
    for s, v in top(pr):
        print(f"  {s:30s} {v:.4f}")
    bar_chart(top(pr), "Paris Metro: PageRank", "PageRank score", FIG / "pagerank.png")

    # 4) Longest fastest journey (weighted diameter) and closeness
    worst = (0.0, None, None)
    avg_time = {}
    for s in net.stations:
        dist, _ = dijkstra(net.adj, net.platforms_of(s))
        per_station = {}
        for pid, d in dist.items():
            name = net.platforms[pid].name
            per_station[name] = min(d, per_station.get(name, float("inf")))
        avg_time[s] = sum(per_station.values()) / (len(per_station) - 1)
        far = max(per_station, key=per_station.get)
        if per_station[far] > worst[0]:
            worst = (per_station[far], s, far)
    print(f"\nLongest fastest journey: {worst[1]} -> {worst[2]}, {worst[0] / 60:.0f} min")
    print("\nMost central stations (lowest average travel time to every other station):")
    for s, t in sorted(avg_time.items(), key=lambda kv: kv[1])[:5]:
        print(f"  {s:30s} {t / 60:.1f} min on average")


if __name__ == "__main__":
    main()
