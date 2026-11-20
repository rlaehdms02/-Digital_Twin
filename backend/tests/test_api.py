import pytest
from fastapi.testclient import TestClient

from app.main import app, state

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_state():
    """테스트마다 상황을 평상시로 초기화한다."""
    state.reset()
    yield
    state.reset()


# ---------- 기본 조회 ----------
def test_health():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["node_count"] == 6


def test_unknown_node_is_404():
    assert client.get("/nodes/P9").status_code == 404
    assert client.get("/route/P9").status_code == 404


# ---------- 시나리오 ----------
def test_normal_route():
    route = client.get("/route/P1").json()
    assert route["path"] == ["P1", "P2", "P3", "P4", "Exit_A"]
    assert route["distance_m"] == 36.0


def test_scenario1_fire_near_p2():
    client.post("/event/fire", json={"node_id": "P2", "block_edges": ["E_P2_P3"]})
    route = client.get("/route/P1").json()
    assert route["path"] == ["P1", "P5", "P3", "P4", "Exit_A"]


def test_scenario2_fire_near_p5():
    client.post("/event/fire", json={"node_id": "P5", "block_edges": ["E_P5_P3"]})
    route = client.get("/route/P1").json()
    assert route["path"] == ["P1", "P2", "P3", "P4", "Exit_A"]


def test_scenario3_exit_blocked():
    client.post("/event/block", json={"edge_id": "E_P4_EXIT"})
    route = client.get("/route/P1").json()
    assert route["reachable"] is False


def test_reset_restores_normal_route():
    client.post("/event/block", json={"edge_id": "E_P2_P3"})
    client.post("/event/reset")
    assert client.get("/route/P1").json()["path"][1] == "P2"


def test_block_unknown_edge_is_404():
    assert client.post("/event/block", json={"edge_id": "NOPE"}).status_code == 404


# ---------- WebSocket ----------
def test_websocket_receives_new_route_on_fire():
    with client.websocket_connect("/ws/P1") as ws:
        first = ws.receive_json()
        assert first["route"]["path"][1] == "P2"

        client.post("/event/fire", json={"node_id": "P2", "block_edges": ["E_P2_P3"]})

        update = ws.receive_json()
        assert update["type"] == "route_update"
        assert update["route"]["path"] == ["P1", "P5", "P3", "P4", "Exit_A"]
        assert update["state"]["emergency"] is True