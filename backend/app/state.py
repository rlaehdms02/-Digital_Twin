from datetime import datetime


class EmergencyState:
    """화재·차단 같은 '지금 이 순간'의 상황. 서버 메모리에 보관한다."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.blocked_edges: set[str] = set()
        self.fires: list[dict] = []

    def block(self, edge_id: str):
        self.blocked_edges.add(edge_id)

    def unblock(self, edge_id: str):
        self.blocked_edges.discard(edge_id)

    def add_fire(self, node_id: str, block_edges: list[str]):
        self.fires.append({
            "node_id": node_id,
            "block_edges": block_edges,
            "time": datetime.now().isoformat(timespec="seconds"),
        })
        for edge_id in block_edges:
            self.block(edge_id)

    def to_dict(self) -> dict:
        return {
            "blocked_edges": sorted(self.blocked_edges),
            "fires": self.fires,
            "emergency": bool(self.fires or self.blocked_edges),
        }