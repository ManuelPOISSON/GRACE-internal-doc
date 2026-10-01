from __future__ import annotations

import copy
import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pipeline_web


def sample_pipeline() -> dict[str, object]:
    return {
        "version": 1,
        "canvas": {"width": 1200, "height": 800},
        "nodes": [
            {
                "id": "input",
                "kind": "file",
                "title": "Input",
                "role": "Input file",
                "description": "",
                "path": "data/input.json",
                "x": 40,
                "y": 50,
                "width": 220,
                "color": "#EDF0F2",
                "details": [],
            },
            {
                "id": "agent",
                "kind": "agent",
                "title": "A2",
                "role": "Agent",
                "description": "Processes the input.",
                "path": "",
                "x": 420,
                "y": 50,
                "width": 240,
                "color": "#FFFFFF",
                "details": ["First detail"],
            },
        ],
        "edges": [
            {
                "id": "input-agent",
                "source": "input",
                "target": "agent",
                "label": "input",
                "color": "#91A0AD",
                "style": "solid",
            }
        ],
    }


class PipelineValidationTests(unittest.TestCase):
    def test_normalizes_valid_pipeline(self) -> None:
        normalized = pipeline_web.validate_pipeline(sample_pipeline())

        self.assertEqual(normalized["nodes"][0]["color"], "#edf0f2")
        self.assertEqual(normalized["edges"][0]["color"], "#91a0ad")
        self.assertEqual(normalized["canvas"]["width"], 1200.0)

    def test_rejects_duplicate_node_id(self) -> None:
        payload = sample_pipeline()
        payload["nodes"].append(copy.deepcopy(payload["nodes"][0]))

        with self.assertRaisesRegex(
            pipeline_web.PipelineValidationError, "Duplicate node id"
        ):
            pipeline_web.validate_pipeline(payload)

    def test_rejects_edge_with_unknown_node(self) -> None:
        payload = sample_pipeline()
        payload["edges"][0]["target"] = "missing"

        with self.assertRaisesRegex(
            pipeline_web.PipelineValidationError, "unknown node"
        ):
            pipeline_web.validate_pipeline(payload)

    def test_rejects_unsafe_file_paths(self) -> None:
        for unsafe_path in ("/etc/passwd", "C:/secret.txt", "../secret", "a/./b"):
            with self.subTest(path=unsafe_path):
                payload = sample_pipeline()
                payload["nodes"][0]["path"] = unsafe_path
                with self.assertRaises(pipeline_web.PipelineValidationError):
                    pipeline_web.validate_pipeline(payload)

    def test_save_is_atomic_and_loads_normalized_data(self) -> None:
        with TemporaryDirectory() as directory:
            graph_path = Path(directory) / "nested" / "pipeline.json"

            saved = pipeline_web.save_pipeline(graph_path, sample_pipeline())

            self.assertEqual(pipeline_web.load_pipeline(graph_path), saved)
            self.assertFalse(graph_path.with_suffix(".json.tmp").exists())

    def test_repository_pipeline_is_valid(self) -> None:
        graph = pipeline_web.load_pipeline(pipeline_web.DEFAULT_GRAPH)

        self.assertEqual(len(graph["nodes"]), 25)
        self.assertEqual(len(graph["edges"]), 26)


class PipelineServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.root = root
        self.graph_path = root / "pipeline.json"
        self.html_path = root / "b1_pipeline.html"
        pipeline_web.save_pipeline(self.graph_path, sample_pipeline())
        self.html_path.write_text("<!doctype html><title>B1 Pipeline</title>", encoding="utf-8")
        self.opened_paths: list[Path] = []
        self.server = pipeline_web.create_server(
            self.graph_path,
            port=0,
            html_path=self.html_path,
            path_opener=self.opened_paths.append,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary_directory.cleanup()

    def request_json(
        self,
        path: str,
        *,
        method: str = "GET",
        payload: object | None = None,
    ) -> tuple[int, dict[str, object]]:
        data = None
        headers: dict[str, str] = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method=method,
        )
        with urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read())

    def test_serves_page_health_and_pipeline(self) -> None:
        with urlopen(self.base_url + "/", timeout=2) as response:
            page = response.read().decode("utf-8")

        health_status, health = self.request_json("/api/health")
        graph_status, graph = self.request_json("/api/pipeline")

        self.assertIn("B1 Pipeline", page)
        self.assertEqual((health_status, health), (200, {"status": "ok"}))
        self.assertEqual(graph_status, 200)
        self.assertEqual(len(graph["nodes"]), 2)

    def test_put_persists_pipeline(self) -> None:
        payload = sample_pipeline()
        payload["nodes"][1]["x"] = 777

        status, response = self.request_json(
            "/api/pipeline", method="PUT", payload=payload
        )

        self.assertEqual(status, 200)
        self.assertEqual(response["nodes"][1]["x"], 777.0)
        self.assertEqual(pipeline_web.load_pipeline(self.graph_path), response)

    def test_put_rejects_invalid_pipeline_without_overwriting(self) -> None:
        original = self.graph_path.read_text(encoding="utf-8")
        payload = sample_pipeline()
        payload["edges"][0]["target"] = "missing"
        request = Request(
            self.base_url + "/api/pipeline",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="PUT",
        )

        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=2)

        self.assertEqual(raised.exception.code, 400)
        raised.exception.close()
        self.assertEqual(self.graph_path.read_text(encoding="utf-8"), original)

    def test_post_opens_existing_file_beneath_selected_root(self) -> None:
        target = self.root / "files" / "report.txt"
        target.parent.mkdir()
        target.write_text("report", encoding="utf-8")

        status, response = self.request_json(
            "/api/open-file",
            method="POST",
            payload={"root": str(self.root), "path": "files/report.txt"},
        )

        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "opened")
        self.assertEqual(self.opened_paths, [target.resolve()])

    def test_post_rejects_path_outside_selected_root(self) -> None:
        request = Request(
            self.base_url + "/api/open-file",
            data=json.dumps({"root": str(self.root), "path": "../secret.txt"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=2)

        self.assertEqual(raised.exception.code, 400)
        raised.exception.close()
        self.assertEqual(self.opened_paths, [])


if __name__ == "__main__":
    unittest.main()
