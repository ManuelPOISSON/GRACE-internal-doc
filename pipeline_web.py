from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_GRAPH = ROOT / "research_plan" / "b1_pipeline.json"
HTML_PATH = ROOT / "research_plan" / "b1_pipeline.html"
MAX_BODY_BYTES = 1_000_000
MAX_NODES = 500
MAX_EDGES = 2_000
MAX_TEXT_LENGTH = 2_000
MAX_DETAILS = 40
MAX_PATH_LENGTH = 1_000
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
EDGE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,180}$")
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")
NODE_KINDS = {"agent", "data", "deterministic", "file", "prompt"}
EDGE_STYLES = {"solid", "dashed"}
DEFAULT_NODE_COLOR = "#ffffff"
DEFAULT_EDGE_COLOR = "#91a0ad"


class PipelineValidationError(ValueError):
    pass


def _validate_text(
    value: object,
    field: str,
    maximum: int = MAX_TEXT_LENGTH,
    *,
    required: bool = False,
) -> str:
    if not isinstance(value, str):
        raise PipelineValidationError(f"{field} must be a string.")
    normalized = value.strip()
    if required and not normalized:
        raise PipelineValidationError(f"{field} must not be empty.")
    if len(normalized) > maximum:
        raise PipelineValidationError(f"{field} is too long.")
    return normalized


def _validate_color(value: object, field: str) -> str:
    if not isinstance(value, str) or not COLOR_PATTERN.fullmatch(value):
        raise PipelineValidationError(f"{field} must be a six-digit hex color.")
    return value.lower()


def _validate_number(
    value: object,
    field: str,
    *,
    minimum: float,
    maximum: float,
) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not minimum <= float(value) <= maximum
    ):
        raise PipelineValidationError(f"{field} must be between {minimum} and {maximum}.")
    return round(float(value), 2)


def _validate_relative_path(value: object) -> str:
    path = _validate_text(value, "Node path", MAX_PATH_LENGTH)
    if not path:
        return ""
    normalized = path.replace("\\", "/")
    if normalized.startswith("/") or WINDOWS_DRIVE_PATTERN.match(normalized):
        raise PipelineValidationError("Node path must be relative to the selected file root.")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PipelineValidationError("Node path contains an unsafe segment.")
    return "/".join(parts)


def validate_pipeline(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise PipelineValidationError("Pipeline must be an object.")
    if payload.get("version") != 1:
        raise PipelineValidationError("Pipeline must use version 1.")

    raw_canvas = payload.get("canvas")
    raw_nodes = payload.get("nodes")
    raw_edges = payload.get("edges")
    if not isinstance(raw_canvas, dict):
        raise PipelineValidationError("Pipeline needs a canvas object.")
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        raise PipelineValidationError("Pipeline needs node and edge lists.")
    if len(raw_nodes) > MAX_NODES or len(raw_edges) > MAX_EDGES:
        raise PipelineValidationError("Pipeline exceeds its size limit.")

    canvas = {
        "width": _validate_number(
            raw_canvas.get("width"), "Canvas width", minimum=400, maximum=100_000
        ),
        "height": _validate_number(
            raw_canvas.get("height"), "Canvas height", minimum=300, maximum=100_000
        ),
    }

    node_ids: set[str] = set()
    nodes: list[dict[str, Any]] = []
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            raise PipelineValidationError("Every node must be an object.")
        node_id = raw.get("id")
        if not isinstance(node_id, str) or not ID_PATTERN.fullmatch(node_id):
            raise PipelineValidationError("Every node needs a safe, non-empty id.")
        if node_id in node_ids:
            raise PipelineValidationError(f"Duplicate node id: {node_id}")
        kind = raw.get("kind")
        if kind not in NODE_KINDS:
            raise PipelineValidationError(f"Node {node_id} has an invalid kind.")
        raw_details = raw.get("details", [])
        if not isinstance(raw_details, list) or len(raw_details) > MAX_DETAILS:
            raise PipelineValidationError(f"Node {node_id} has invalid details.")
        details = [
            _validate_text(item, "Node detail", 300, required=True)
            for item in raw_details
        ]
        nodes.append(
            {
                "id": node_id,
                "kind": kind,
                "title": _validate_text(raw.get("title"), "Node title", 300, required=True),
                "role": _validate_text(raw.get("role", ""), "Node role", 120),
                "description": _validate_text(
                    raw.get("description", ""), "Node description"
                ),
                "path": _validate_relative_path(raw.get("path", "")),
                "x": _validate_number(
                    raw.get("x"), f"Node {node_id} x", minimum=-100_000, maximum=100_000
                ),
                "y": _validate_number(
                    raw.get("y"), f"Node {node_id} y", minimum=-100_000, maximum=100_000
                ),
                "width": _validate_number(
                    raw.get("width", 260),
                    f"Node {node_id} width",
                    minimum=80,
                    maximum=1_000,
                ),
                "color": _validate_color(
                    raw.get("color", DEFAULT_NODE_COLOR), "Node color"
                ),
                "details": details,
            }
        )
        node_ids.add(node_id)

    edge_ids: set[str] = set()
    edges: list[dict[str, Any]] = []
    for raw in raw_edges:
        if not isinstance(raw, dict):
            raise PipelineValidationError("Every edge must be an object.")
        edge_id = raw.get("id")
        source = raw.get("source")
        target = raw.get("target")
        if not isinstance(edge_id, str) or not EDGE_ID_PATTERN.fullmatch(edge_id):
            raise PipelineValidationError("Every edge needs a safe, non-empty id.")
        if edge_id in edge_ids:
            raise PipelineValidationError(f"Duplicate edge id: {edge_id}")
        if source not in node_ids or target not in node_ids:
            raise PipelineValidationError(f"Edge {edge_id} references an unknown node.")
        style = raw.get("style", "solid")
        if style not in EDGE_STYLES:
            raise PipelineValidationError(f"Edge {edge_id} has an invalid style.")
        edges.append(
            {
                "id": edge_id,
                "source": source,
                "target": target,
                "label": _validate_text(raw.get("label", ""), "Edge label", 200),
                "color": _validate_color(
                    raw.get("color", DEFAULT_EDGE_COLOR), "Edge color"
                ),
                "style": style,
            }
        )
        edge_ids.add(edge_id)

    return {"version": 1, "canvas": canvas, "nodes": nodes, "edges": edges}


def load_pipeline(path: Path) -> dict[str, Any]:
    return validate_pipeline(json.loads(path.read_text(encoding="utf-8")))


def save_pipeline(path: Path, payload: object) -> dict[str, Any]:
    normalized = validate_pipeline(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return normalized


def resolve_open_path(root_value: object, path_value: object) -> Path:
    root_text = _validate_text(root_value, "File root", MAX_PATH_LENGTH, required=True)
    relative_path = _validate_relative_path(path_value)
    if not relative_path:
        raise PipelineValidationError("File path must not be empty.")
    root = Path(root_text).expanduser()
    if not root.is_absolute():
        raise PipelineValidationError("File root must be an absolute path.")
    resolved_root = root.resolve(strict=True)
    target = (resolved_root / relative_path).resolve(strict=True)
    try:
        target.relative_to(resolved_root)
    except ValueError as error:
        raise PipelineValidationError("File path escapes the selected root.") from error
    return target


def open_local_path(path: Path) -> None:
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
        return
    command = ["open", str(path)] if sys.platform == "darwin" else ["xdg-open", str(path)]
    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def make_handler(
    graph_path: Path,
    html_path: Path = HTML_PATH,
    path_opener: Callable[[Path], None] = open_local_path,
) -> type[BaseHTTPRequestHandler]:
    write_lock = threading.Lock()

    class PipelineHandler(BaseHTTPRequestHandler):
        def _send_bytes(
            self,
            status: HTTPStatus,
            content_type: str,
            body: bytes,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self' blob:; style-src 'unsafe-inline'; "
                "script-src 'unsafe-inline'; connect-src 'self'; "
                "img-src 'self' data: blob:; object-src 'none'; base-uri 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: HTTPStatus, payload: object) -> None:
            self._send_bytes(
                status,
                "application/json; charset=utf-8",
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            )

        def do_GET(self) -> None:
            request = urlparse(self.path)
            if request.path in {"/", "/b1_pipeline.html"}:
                try:
                    self._send_bytes(
                        HTTPStatus.OK,
                        "text/html; charset=utf-8",
                        html_path.read_bytes(),
                    )
                except OSError as error:
                    self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {"error": f"Could not load pipeline page: {error}"},
                    )
                return
            if request.path == "/api/health":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return
            if request.path == "/api/pipeline":
                try:
                    self._send_json(HTTPStatus.OK, load_pipeline(graph_path))
                except (OSError, json.JSONDecodeError, PipelineValidationError) as error:
                    self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {"error": f"Could not load pipeline: {error}"},
                    )
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found."})

        def do_PUT(self) -> None:
            request = urlparse(self.path)
            if request.path != "/api/pipeline":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid body length."})
                return
            if length <= 0 or length > MAX_BODY_BYTES:
                self._send_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    {"error": "Invalid body size."},
                )
                return
            try:
                payload = json.loads(self.rfile.read(length))
                with write_lock:
                    normalized = save_pipeline(graph_path, payload)
            except json.JSONDecodeError:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "Body must be valid JSON."},
                )
                return
            except PipelineValidationError as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                return
            except OSError as error:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": f"Could not save pipeline: {error}"},
                )
                return
            self._send_json(HTTPStatus.OK, normalized)

        def do_POST(self) -> None:
            request = urlparse(self.path)
            if request.path != "/api/open-file":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid body length."})
                return
            if length <= 0 or length > MAX_BODY_BYTES:
                self._send_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    {"error": "Invalid body size."},
                )
                return
            try:
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise PipelineValidationError("Open-file request must be an object.")
                target = resolve_open_path(payload.get("root"), payload.get("path"))
                path_opener(target)
            except json.JSONDecodeError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Body must be valid JSON."})
                return
            except PipelineValidationError as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                return
            except FileNotFoundError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "File does not exist."})
                return
            except OSError as error:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": f"Could not open file: {error}"},
                )
                return
            self._send_json(
                HTTPStatus.OK,
                {"status": "opened", "path": str(target)},
            )

        def log_message(self, format_string: str, *args: object) -> None:
            return

    return PipelineHandler


def create_server(
    graph_path: Path = DEFAULT_GRAPH,
    host: str = "127.0.0.1",
    port: int = 8002,
    html_path: Path = HTML_PATH,
    path_opener: Callable[[Path], None] = open_local_path,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        (host, port),
        make_handler(graph_path.resolve(), html_path.resolve(), path_opener),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the editable B1 pipeline graph.")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8002)
    args: argparse.Namespace = parser.parse_args()
    load_pipeline(args.graph)
    server = create_server(args.graph, args.host, args.port)
    print(f"Editable B1 pipeline: http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
