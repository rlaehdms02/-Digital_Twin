import networkx as nx


def build_graph(building: dict, blocked: set[str] | None = None) -> nx.Graph:
    """노드·엣지 데이터로 NetworkX 그래프를 만든다. blocked 에 든 엣지는 뺀다."""
    blocked = blocked or set()
    g = nx.Graph()

    for node_id in building["nodes"]:
        g.add_node(node_id)

    for edge in building["edges"].values():
        if edge["id"] in blocked:
            continue
        g.add_edge(edge["from"], edge["to"], weight=edge["length_m"], edge_id=edge["id"])

    return g


def find_route(building: dict, start: str, blocked: set[str] | None = None) -> dict:
    """start 에서 가장 가까운 출구까지 경로를 찾는다."""
    g = build_graph(building, blocked)
    exits = [n["id"] for n in building["nodes"].values() if n["type"] == "exit"]

    best = None
    for exit_id in exits:
        try:
            length, path = nx.single_source_dijkstra(g, start, exit_id, weight="weight")
        except nx.NetworkXNoPath:
            continue
        if best is None or length < best["distance_m"]:
            best = {"distance_m": length, "path": path}

    if best is None:
        return {"reachable": False, "start": start, "path": [], "distance_m": None}

    edge_ids = [g.edges[a, b]["edge_id"] for a, b in zip(best["path"], best["path"][1:])]
    return {
        "reachable": True,
        "start": start,
        "exit": best["path"][-1],
        "path": best["path"],
        "edges": edge_ids,
        "distance_m": best["distance_m"],
    }