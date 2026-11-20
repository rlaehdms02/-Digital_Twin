from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.data_loader import load_building
from app.routing import find_route
from app.state import EmergencyState
from app.ws import ConnectionManager

app = FastAPI(title="SafeExit API", version="0.1.0")

# 서버가 켜질 때 한 번만 읽어서 메모리에 보관
building = load_building()
state = EmergencyState()
manager = ConnectionManager()


# ---------- 요청 바디 모양 정의 ----------
class BlockRequest(BaseModel):
    edge_id: str


class FireRequest(BaseModel):
    node_id: str
    block_edges: list[str] = []


# ---------- 공통 함수 ----------
def check_node(node_id: str):
    if node_id not in building["nodes"]:
        raise HTTPException(status_code=404, detail=f"노드 {node_id} 없음")


def check_edge(edge_id: str):
    if edge_id not in building["edges"]:
        raise HTTPException(status_code=404, detail=f"엣지 {edge_id} 없음")


def route_message(node_id: str) -> dict:
    """WebSocket 으로 보낼 메시지: 현재 상황 + 이 노드에서의 경로"""
    return {
        "type": "route_update",
        "state": state.to_dict(),
        "route": find_route(building, node_id, state.blocked_edges),
    }


async def notify_all():
    await manager.broadcast(route_message)


# ---------- 조회 ----------
@app.get("/")
def health():
    return {
        "status": "ok",
        "message": "SafeExit 서버 OK",
        "node_count": len(building["nodes"]),
        "edge_count": len(building["edges"]),
        "ws_clients": len(manager.clients),
    }


@app.get("/nodes")
def list_nodes():
    return list(building["nodes"].values())


@app.get("/nodes/{node_id}")
def get_node(node_id: str):
    check_node(node_id)
    return building["nodes"][node_id]


@app.get("/edges")
def list_edges():
    return list(building["edges"].values())


@app.get("/route/{node_id}")
def get_route(node_id: str):
    check_node(node_id)
    return find_route(building, node_id, state.blocked_edges)


@app.get("/state")
def get_state():
    return state.to_dict()


# ---------- 관리자 이벤트 (바뀌면 모두에게 알림) ----------
@app.post("/event/block")
async def block_edge(req: BlockRequest):
    check_edge(req.edge_id)
    state.block(req.edge_id)
    await notify_all()
    return state.to_dict()


@app.post("/event/unblock")
async def unblock_edge(req: BlockRequest):
    check_edge(req.edge_id)
    state.unblock(req.edge_id)
    await notify_all()
    return state.to_dict()


@app.post("/event/fire")
async def report_fire(req: FireRequest):
    check_node(req.node_id)
    for edge_id in req.block_edges:
        check_edge(edge_id)
    state.add_fire(req.node_id, req.block_edges)
    await notify_all()
    return state.to_dict()


@app.post("/event/reset")
async def reset():
    state.reset()
    await notify_all()
    return state.to_dict()


# ---------- WebSocket ----------
@app.websocket("/ws/{node_id}")
async def websocket_endpoint(ws: WebSocket, node_id: str):
    if node_id not in building["nodes"]:
        await ws.close(code=4404)
        return
    await manager.connect(ws, node_id)
    await ws.send_json(route_message(node_id))  # 접속하자마자 현재 경로 1회 전송
    try:
        while True:
            await ws.receive_text()  # 연결 유지용 (클라이언트 메시지는 지금은 무시)
    except WebSocketDisconnect:
        manager.disconnect(ws)