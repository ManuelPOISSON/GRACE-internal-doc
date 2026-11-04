import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from mindmap_web import (
    MindMapValidationError,
    create_server,
    load_mindmap,
    save_mindmap,
    validate_mindmap,
)


LEGACY_SAMPLE = {
    "version": 1,
    "root": {
        "id": "root",
        "label": "Research plan",
        "note": "",
        "children": [
            {"id": "q1", "label": "Question one", "note": "A note", "children": []}
        ],
    },
}

SAMPLE = {
    "version": 2,
    "nodes": [
        {
            "id": "root",
            "label": "Research plan",
            "note": "",
            "x": 40,
            "y": 80,
            "color": "#dfe7ff",
            "bold": True,
        },
        {
            "id": "q1",
            "label": "Question one",
            "note": "A note",
            "x": 340,
            "y": 80,
            "color": "#dff7ea",
            "bold": False,
        },
        {
            "id": "isolated",
            "label": "Unattached idea",
            "note": "",
            "x": 340,
            "y": 240,
            "color": "#fff0c9",
            "bold": False,
        },
    ],
    "edges": [
        {
            "id": "edge-1",
            "source": "root",
            "target": "q1",
            "kind": "hierarchy",
            "color": "#64748b",
        },
        {
            "id": "edge-2",
            "source": "q1",
            "target": "root",
            "kind": "relation",
            "color": "#b42318",
        },
    ],
}


class MindMapWebTests(unittest.TestCase):
    def test_validation_rejects_duplicate_ids(self) -> None:
        invalid = json.loads(json.dumps(SAMPLE))
        invalid["nodes"].append(json.loads(json.dumps(invalid["nodes"][0])))
        with self.assertRaises(MindMapValidationError):
            validate_mindmap(invalid)

    def test_validation_accepts_cycles_and_isolated_nodes(self) -> None:
        graph = validate_mindmap(SAMPLE)
        self.assertEqual(len(graph["nodes"]), 3)
        self.assertEqual(len(graph["edges"]), 2)
        self.assertEqual(graph["nodes"][2]["id"], "isolated")

    def test_version_one_tree_is_migrated(self) -> None:
        graph = validate_mindmap(LEGACY_SAMPLE)
        self.assertEqual(graph["version"], 2)
        self.assertEqual({node["id"] for node in graph["nodes"]}, {"root", "q1"})
        self.assertEqual(graph["edges"][0]["kind"], "hierarchy")

    def test_validation_rejects_edge_to_unknown_node(self) -> None:
        invalid = json.loads(json.dumps(SAMPLE))
        invalid["edges"][0]["target"] = "missing"
        with self.assertRaises(MindMapValidationError):
            validate_mindmap(invalid)

    def test_save_and_load_normalize_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.json"
            payload = json.loads(json.dumps(SAMPLE))
            payload["nodes"][0]["label"] = "  Research plan  "
            save_mindmap(path, payload)
            loaded = load_mindmap(path)
            self.assertEqual(loaded["nodes"][0]["label"], "Research plan")
            self.assertTrue(loaded["nodes"][0]["bold"])

    def test_live_interface_loads_and_persists_map(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.json"
            save_mindmap(path, SAMPLE)
            server: ThreadingHTTPServer = create_server(path, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(f"{base_url}/", timeout=2) as response:
                    page = response.read().decode("utf-8")
                    self.assertIn("MAL Idea Graph", page)
                    self.assertIn("New isolated idea", page)
                    self.assertIn("Create an edge", page)
                    self.assertIn("Multiple selection", page)
                    self.assertIn("Collapse children", page)
                    self.assertIn("Ctrl + mouse wheel", page)
                    self.assertIn("Ctrl+C / Ctrl+V", page)
                    self.assertIn('id="copy-node"', page)
                    self.assertIn('id="paste-node"', page)
                    self.assertIn("textContent", page)
                with urlopen(f"{base_url}/api/mindmap", timeout=2) as response:
                    payload = json.loads(response.read())
                    self.assertEqual(payload["nodes"][1]["label"], "Question one")
                payload["nodes"][1]["label"] = "Edited question"
                request = Request(
                    f"{base_url}/api/mindmap",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="PUT",
                )
                with urlopen(request, timeout=2) as response:
                    self.assertEqual(response.status, 200)
                self.assertEqual(
                    load_mindmap(path)["nodes"][1]["label"],
                    "Edited question",
                )
                invalid_request = Request(
                    f"{base_url}/api/mindmap",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="PUT",
                )
                with self.assertRaises(HTTPError) as error:
                    urlopen(invalid_request, timeout=2)
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
