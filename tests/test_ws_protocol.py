"""Integration tests for the WebSocket protocol."""

import json
import pytest
from fastapi.testclient import TestClient

from conway.app import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


def test_get_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_static_css(client):
    resp = client.get("/static/css/style.css")
    assert resp.status_code == 200


def test_static_js(client):
    resp = client.get("/static/js/main.js")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# WebSocket helpers
# ---------------------------------------------------------------------------


def ws_send(ws, **kwargs):
    ws.send_text(json.dumps(kwargs))


def ws_recv(ws) -> dict:
    return json.loads(ws.receive_text())


# ---------------------------------------------------------------------------
# WebSocket: init message
# ---------------------------------------------------------------------------


def test_ws_init_message(client):
    with client.websocket_connect("/ws") as ws:
        msg = ws_recv(ws)
        assert msg["type"] == "init"
        assert msg["generation"] == 0
        assert msg["rows"] == 60
        assert msg["cols"] == 80
        assert msg["running"] is False
        assert "presets" in msg
        assert "glider" in msg["presets"]
        assert "cells" in msg


# ---------------------------------------------------------------------------
# WebSocket: step
# ---------------------------------------------------------------------------


def test_ws_step(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        # Load a blinker first
        ws_send(ws, type="load_preset", name="blinker")
        ws_recv(ws)  # state after load
        ws_send(ws, type="step")
        msg = ws_recv(ws)
        assert msg["type"] == "state"
        assert msg["generation"] == 1


# ---------------------------------------------------------------------------
# WebSocket: toggle_cell
# ---------------------------------------------------------------------------


def test_ws_toggle_cell(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        ws_send(ws, type="toggle_cell", row=10, col=10)
        msg = ws_recv(ws)
        assert msg["type"] == "state"
        assert [10, 10] in msg["cells"]
        # Toggle again to kill it
        ws_send(ws, type="toggle_cell", row=10, col=10)
        msg2 = ws_recv(ws)
        assert [10, 10] not in msg2["cells"]


# ---------------------------------------------------------------------------
# WebSocket: set_cells
# ---------------------------------------------------------------------------


def test_ws_set_cells(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        ws_send(ws, type="set_cells", cells=[[1, 1], [2, 2], [3, 3]], alive=True)
        msg = ws_recv(ws)
        assert [1, 1] in msg["cells"]
        assert [2, 2] in msg["cells"]
        assert [3, 3] in msg["cells"]


# ---------------------------------------------------------------------------
# WebSocket: clear
# ---------------------------------------------------------------------------


def test_ws_clear(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        ws_send(ws, type="set_cells", cells=[[5, 5], [6, 6]], alive=True)
        ws_recv(ws)
        ws_send(ws, type="clear")
        msg = ws_recv(ws)
        assert msg["cells"] == []
        assert msg["running"] is False


# ---------------------------------------------------------------------------
# WebSocket: set_speed
# ---------------------------------------------------------------------------


def test_ws_set_speed(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        ws_send(ws, type="set_speed", tps=10.0)
        msg = ws_recv(ws)
        assert msg["tps"] == 10.0


def test_ws_set_speed_clamped(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        ws_send(ws, type="set_speed", tps=999)
        msg = ws_recv(ws)
        assert msg["tps"] <= 30.0
        ws_send(ws, type="set_speed", tps=0)
        msg2 = ws_recv(ws)
        assert msg2["tps"] >= 0.5


# ---------------------------------------------------------------------------
# WebSocket: load_preset
# ---------------------------------------------------------------------------


def test_ws_load_preset_glider(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        ws_send(ws, type="load_preset", name="glider")
        msg = ws_recv(ws)
        assert msg["type"] == "state"
        assert len(msg["cells"]) == 5
        assert msg["generation"] == 0


def test_ws_load_preset_unknown(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        ws_send(ws, type="load_preset", name="fake_pattern_xyz")
        msg = ws_recv(ws)
        assert msg["type"] == "error"
        assert "fake_pattern_xyz" in msg["message"]


# ---------------------------------------------------------------------------
# WebSocket: resize
# ---------------------------------------------------------------------------


def test_ws_resize(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        ws_send(ws, type="resize", rows=30, cols=40)
        msg = ws_recv(ws)
        assert msg["rows"] == 30
        assert msg["cols"] == 40


# ---------------------------------------------------------------------------
# WebSocket: unknown message type
# ---------------------------------------------------------------------------


def test_ws_unknown_type(client):
    with client.websocket_connect("/ws") as ws:
        ws_recv(ws)  # init
        ws_send(ws, type="does_not_exist")
        msg = ws_recv(ws)
        assert msg["type"] == "error"
