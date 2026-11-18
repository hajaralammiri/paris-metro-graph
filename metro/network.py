"""Load the Paris Metro dataset and build a weighted directed graph.

Each node is a *platform*: one station served by one line in one direction.
An edge u -> v carries a travel time in seconds: either a ride between two
consecutive stations, or a walking transfer inside the same station.
"""

from __future__ import annotations

import csv
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class Platform:
    id: int
    name: str
    line: str
    address: str
    direction: str


def normalize(name: str) -> str:
    """Lowercase, strip accents and punctuation so 'Châtelet' == 'chatelet'."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return "".join(c for c in text.lower() if c.isalnum())


class MetroNetwork:
    def __init__(self, platforms: dict[int, Platform], adj: dict[int, dict[int, float]]):
        self.platforms = platforms
        self.adj = adj  # adj[u][v] = travel time in seconds
        self._by_station: dict[str, list[int]] = defaultdict(list)
        for p in platforms.values():
            self._by_station[p.name].append(p.id)

    @classmethod
    def from_csv(cls, data_dir: Path = DATA_DIR) -> "MetroNetwork":
        platforms: dict[int, Platform] = {}
        with open(data_dir / "stations.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pid = int(row["uint32_s_id"])
                platforms[pid] = Platform(
                    id=pid,
                    name=row["string_name_station"].strip(),
                    line=row["string_short_line"].strip(),
                    address=row["string_adress_station"].strip(),
                    direction=row["string_desc_line"].strip(),
                )

        adj: dict[int, dict[int, float]] = {pid: {} for pid in platforms}
        with open(data_dir / "connections.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                u, v = int(row["uint32_from_stop_id"]), int(row["uint32_to_stop_id"])
                w = float(row["uint32_min_transfer_time"])
                if u == v:  # self-loops carry no information
                    continue
                # keep the fastest connection if the pair appears twice
                if v not in adj[u] or w < adj[u][v]:
                    adj[u][v] = w
        return cls(platforms, adj)

    # ---- stations -------------------------------------------------------
    @property
    def stations(self) -> list[str]:
        return sorted(self._by_station)

    def platforms_of(self, station: str) -> list[int]:
        return self._by_station[station]

    def find_station(self, query: str) -> str:
        """Return the station whose name best matches `query`."""
        q = normalize(query)
        exact = [s for s in self._by_station if normalize(s) == q]
        if exact:
            return exact[0]
        # prefer names that start with the query, then the shortest match
        partial = sorted((s for s in self._by_station if q in normalize(s)),
                         key=lambda s: (not normalize(s).startswith(q), len(s)))
        if partial:
            return partial[0]
        raise KeyError(f"No station matches {query!r}")

    def is_transfer(self, u: int, v: int) -> bool:
        return self.platforms[u].name == self.platforms[v].name

    # ---- station-level graph -------------------------------------------
    def station_graph(self) -> dict[str, dict[str, float]]:
        """Undirected graph whose nodes are station names (lines merged).

        Weight = fastest ride between the two stations. Used for centrality
        and PageRank, where we care about stations, not platforms.
        """
        g: dict[str, dict[str, float]] = {s: {} for s in self._by_station}
        for u, nbrs in self.adj.items():
            a = self.platforms[u].name
            for v, w in nbrs.items():
                b = self.platforms[v].name
                if a == b:
                    continue
                if b not in g[a] or w < g[a][b]:
                    g[a][b] = g[b][a] = w
        return g

    def __repr__(self) -> str:
        n_edges = sum(len(v) for v in self.adj.values())
        return (f"MetroNetwork({len(self._by_station)} stations, "
                f"{len(self.platforms)} platforms, {n_edges} connections)")
