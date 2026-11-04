from __future__ import annotations

import argparse
import json
import math
import re
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_MAP = ROOT / "research_plan" / "research_mindmap.json"
HTML_PATH = ROOT / "research_plan" / "mindmap.html"
MAX_BODY_BYTES = 1_000_000
MAX_NODES = 500
MAX_EDGES = 2_000
MAX_DEPTH = 20
MAX_LABEL_LENGTH = 300
MAX_NOTE_LENGTH = 2_000
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
EDGE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,180}$")
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
EDGE_KINDS = {"hierarchy", "relation"}
DEFAULT_NODE_COLOR = "#dfe7ff"
DEFAULT_EDGE_COLOR = "#64748b"


class MindMapValidationError(ValueError):
    pass


def _validate_text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str) or (field == "label" and not value.strip()):
        raise MindMapValidationError(f"{field.capitalize()} must be a string.")
    if len(value) > maximum:
        raise MindMapValidationError(f"{field.capitalize()} is too long.")
    return value.strip()


def _validate_color(value: object, field: str) -> str:
    if not isinstance(value, str) or not COLOR_PATTERN.fullmatch(value):
        raise MindMapValidationError(f"{field} must be a six-digit hex color.")
    return value.lower()


def _migrate_tree(payload: dict[str, Any]) -> dict[str, Any]:
    if "root" not in payload:
        raise MindMapValidationError("Version 1 mind map needs a root node.")
    seen: set[str] = set()
    count = 0
    edge_count = 0
    leaf = 0
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    palette = ["#dfe7ff", "#dff7ea", "#fff0c9", "#f1e3ff", "#dff4ff"]

    def migrate_node(raw: object, depth: int, parent_id: str | None = None) -> float:
        nonlocal count, edge_count, leaf
        if depth > MAX_DEPTH:
            raise MindMapValidationError(f"Mind map exceeds maximum depth {MAX_DEPTH}.")
        if not isinstance(raw, dict):
            raise MindMapValidationError("Every node must be an object.")
        node_id = raw.get("id")
        label = _validate_text(raw.get("label"), "label", MAX_LABEL_LENGTH)
        note = _validate_text(raw.get("note", ""), "note", MAX_NOTE_LENGTH)
        children = raw.get("children")
        if not isinstance(node_id, str) or not ID_PATTERN.fullmatch(node_id):
            raise MindMapValidationError("Every node needs a safe, non-empty id.")
        if node_id in seen:
            raise MindMapValidationError(f"Duplicate node id: {node_id}")
        if not isinstance(children, list):
            raise MindMapValidationError(f"Node {node_id} children must be a list.")
        seen.add(node_id)
        count += 1
        if count > MAX_NODES:
            raise MindMapValidationError(f"Mind map exceeds maximum size {MAX_NODES}.")
        node = {
            "id": node_id,
            "label": label,
            "note": note,
            "x": 50 + depth * 300,
            "y": 0,
            "color": palette[depth % len(palette)],
            "bold": depth == 0,
        }
        nodes.append(node)
        if parent_id is not None:
            edge_count += 1
            edges.append({
                "id": f"tree-edge-{edge_count}",
                "source": parent_id,
                "target": node_id,
                "kind": "hierarchy",
                "color": DEFAULT_EDGE_COLOR,
            })
        child_positions = [migrate_node(child, depth + 1, node_id) for child in children]
        if child_positions:
            y = (child_positions[0] + child_positions[-1]) / 2
        else:
            y = 70 + leaf * 100
            leaf += 1
        node["y"] = y
        return y

    migrate_node(payload["root"], 0)
    return {"version": 2, "nodes": nodes, "edges": edges}


def validate_mindmap(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise MindMapValidationError("Mind map must be an object.")
    if payload.get("version") == 1:
        payload = _migrate_tree(payload)
    if payload.get("version") != 2:
        raise MindMapValidationError("Idea graph must use version 2.")
    raw_nodes = payload.get("nodes")
    raw_edges = payload.get("edges")
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        raise MindMapValidationError("Idea graph needs node and edge lists.")
    if len(raw_nodes) > MAX_NODES or len(raw_edges) > MAX_EDGES:
        raise MindMapValidationError("Idea graph exceeds its size limit.")

    node_ids: set[str] = set()
    nodes: list[dict[str, Any]] = []
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            raise MindMapValidationError("Every node must be an object.")
        node_id = raw.get("id")
        if not isinstance(node_id, str) or not ID_PATTERN.fullmatch(node_id):
            raise MindMapValidationError("Every node needs a safe, non-empty id.")
        if node_id in node_ids:
            raise MindMapValidationError(f"Duplicate node id: {node_id}")
        x = raw.get("x", 0)
        y = raw.get("y", 0)
        if (
            isinstance(x, bool) or isinstance(y, bool)
            or not isinstance(x, (int, float)) or not isinstance(y, (int, float))
            or not math.isfinite(x) or not math.isfinite(y)
            or abs(x) > 100_000 or abs(y) > 100_000
        ):
            raise MindMapValidationError(f"Node {node_id} has invalid coordinates.")
        bold = raw.get("bold", False)
        if not isinstance(bold, bool):
            raise MindMapValidationError(f"Node {node_id} bold must be boolean.")
        nodes.append({
            "id": node_id,
            "label": _validate_text(raw.get("label"), "label", MAX_LABEL_LENGTH),
            "note": _validate_text(raw.get("note", ""), "note", MAX_NOTE_LENGTH),
            "x": round(float(x), 2),
            "y": round(float(y), 2),
            "color": _validate_color(raw.get("color", DEFAULT_NODE_COLOR), "Node color"),
            "bold": bold,
        })
        node_ids.add(node_id)

    edge_ids: set[str] = set()
    edges: list[dict[str, Any]] = []
    for raw in raw_edges:
        if not isinstance(raw, dict):
            raise MindMapValidationError("Every edge must be an object.")
        edge_id = raw.get("id")
        source = raw.get("source")
        target = raw.get("target")
        kind = raw.get("kind", "relation")
        if not isinstance(edge_id, str) or not EDGE_ID_PATTERN.fullmatch(edge_id):
            raise MindMapValidationError("Every edge needs a safe, non-empty id.")
        if edge_id in edge_ids:
            raise MindMapValidationError(f"Duplicate edge id: {edge_id}")
        if source not in node_ids or target not in node_ids:
            raise MindMapValidationError(f"Edge {edge_id} references an unknown node.")
        if kind not in EDGE_KINDS:
            raise MindMapValidationError(f"Edge {edge_id} has an invalid kind.")
        edges.append({
            "id": edge_id,
            "source": source,
            "target": target,
            "kind": kind,
            "color": _validate_color(raw.get("color", DEFAULT_EDGE_COLOR), "Edge color"),
        })
        edge_ids.add(edge_id)
    return {"version": 2, "nodes": nodes, "edges": edges}


def load_mindmap(path: Path) -> dict[str, Any]:
    return validate_mindmap(json.loads(path.read_text(encoding="utf-8")))


def save_mindmap(path: Path, payload: object) -> dict[str, Any]:
    normalized = validate_mindmap(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return normalized


def make_handler(map_path: Path) -> type[BaseHTTPRequestHandler]:
    write_lock = threading.Lock()

    class MindMapHandler(BaseHTTPRequestHandler):
        def _send_bytes(
            self, status: HTTPStatus, content_type: str, body: bytes
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'unsafe-inline'; "
                "script-src 'unsafe-inline'; connect-src 'self'; "
                "img-src 'self' data:; object-src 'none'; base-uri 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _send_json(
            self, status: HTTPStatus, payload: object
        ) -> None:
            self._send_bytes(
                status,
                "application/json; charset=utf-8",
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            )

        def do_GET(self) -> None:
            request = urlparse(self.path)
            if request.path == "/":
                self._send_bytes(
                    HTTPStatus.OK,
                    "text/html; charset=utf-8",
                    HTML_PATH.read_bytes(),
                )
                return
            if request.path == "/api/health":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return
            if request.path == "/api/mindmap":
                try:
                    self._send_json(HTTPStatus.OK, load_mindmap(map_path))
                except (OSError, json.JSONDecodeError, MindMapValidationError) as error:
                    self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {"error": f"Could not load mind map: {error}"},
                    )
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found."})

        def do_PUT(self) -> None:
            request = urlparse(self.path)
            if request.path != "/api/mindmap":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid body length."})
                return
            if length <= 0 or length > MAX_BODY_BYTES:
                self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "Invalid body size."})
                return
            try:
                payload = json.loads(self.rfile.read(length))
                with write_lock:
                    normalized = save_mindmap(map_path, payload)
            except json.JSONDecodeError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Body must be valid JSON."})
                return
            except MindMapValidationError as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                return
            except OSError as error:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Could not save: {error}"})
                return
            self._send_json(HTTPStatus.OK, normalized)

        def log_message(self, format_string: str, *args: object) -> None:
            return

    return MindMapHandler


def create_server(
    map_path: Path = DEFAULT_MAP,
    host: str = "127.0.0.1",
    port: int = 8001,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(map_path.resolve()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the editable MAL research mind map.")
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args: argparse.Namespace = parser.parse_args()
    load_mindmap(args.map)
    server = create_server(args.map, args.host, args.port)
    print(
        f"Editable MAL research mind map: http://{args.host}:{server.server_port}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
