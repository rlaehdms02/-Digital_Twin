from fastapi import WebSocket


class ConnectionManager:
    """연결된 화면(휴대폰·Unity)을 기억했다가 한꺼번에 메시지를 보낸다."""

    def __init__(self):
        # (웹소켓, 그 화면이 있는 노드 id) 목록
        self.clients: list[tuple[WebSocket, str]] = []

    async def connect(self, ws: WebSocket, node_id: str):
        await ws.accept()
        self.clients.append((ws, node_id))

    def disconnect(self, ws: WebSocket):
        self.clients = [(w, n) for (w, n) in self.clients if w is not ws]

    async def broadcast(self, make_message):
        """make_message(node_id) 로 각 화면에 맞는 메시지를 만들어 보낸다."""
        dead = []
        for ws, node_id in self.clients:
            try:
                await ws.send_json(make_message(node_id))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)