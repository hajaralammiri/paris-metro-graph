"""Find the fastest metro route between two stations.

Usage:
    python route.py "Châtelet" "Nation"
    python route.py "la defense" "gare de lyon"
"""

import sys

from metro.algorithms import shortest_path
from metro.network import MetroNetwork


def describe(net: MetroNetwork, path: list[int]) -> list[str]:
    """Turn a list of platforms into human-readable steps, grouped by line."""
    steps = []
    i = 0
    while i < len(path) - 1:
        u = path[i]
        if net.is_transfer(u, path[i + 1]):
            # several platform hops inside one station = one change
            while i < len(path) - 1 and net.is_transfer(path[i], path[i + 1]):
                i += 1
            if i == len(path) - 1:
                break
            new_line = net.platforms[path[i]].line
            if new_line != net.platforms[u].line:
                steps.append(f"  Change at {net.platforms[u].name} -> line {new_line}")
            continue
        line, start, stops = net.platforms[u].line, net.platforms[u].name, 0
        while i < len(path) - 1 and not net.is_transfer(path[i], path[i + 1]):
            i += 1
            stops += 1
        end = net.platforms[path[i]].name
        steps.append(f"  Line {line}: {start} -> {end} ({stops} stop{'s' * (stops > 1)})")
    return steps


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        print(__doc__)
        sys.exit(1)
    net = MetroNetwork.from_csv()
    a, b = net.find_station(argv[1]), net.find_station(argv[2])
    seconds, path = shortest_path(net.adj, net.platforms_of(a), net.platforms_of(b))
    if not path:
        print(f"No route between {a} and {b}")
        return
    print(f"{a} -> {b}: about {round(seconds / 60)} min")
    print("\n".join(describe(net, path)))


if __name__ == "__main__":
    main(sys.argv)
