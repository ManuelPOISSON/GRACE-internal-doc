import json
import threading
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from mal_rag import Chunk, Index
from rag_web import PublicationFiles, create_server, load_publication_files, query_payload


class RagWebTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = Index([
            Chunk(
                id="paper:1",
                source="research-papers/extracted/paper.md",
                repository="research-papers",
                title="MAL validation — 3. Results (page 4)",
                text="### 3. Results\nMAL covers attack techniques.",
                kind="paper",
                page=4,
                doi="10.1000/mal",
                section="3. Results",
            )
        ])

    def test_query_payload_contains_answer_and_sources(self) -> None:
        payload = query_payload(self.index, "attack techniques", limit=1)
        self.assertIn("MAL covers", payload["answer"])
        self.assertEqual(payload["sources"][0]["page"], 4)
        self.assertEqual(payload["sources"][0]["section"], "3. Results")
        self.assertEqual(payload["sources"][0]["url"], "https://doi.org/10.1000/mal")
        self.assertFalse(payload["sources"][0]["local_pdf"])

    def test_cataloged_local_pdf_is_preferred(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_dir = root / "pdfs"
            pdf_dir.mkdir()
            (pdf_dir / "paper.pdf").write_bytes(b"%PDF-1.4\nlocal test")
            catalog = root / "catalog.json"
            catalog.write_text(
                json.dumps({"papers": [{"id": "paper", "pdf": "paper.pdf"}]}),
                encoding="utf-8",
            )
            publications = load_publication_files(catalog)
            payload = query_payload(self.index, "attack techniques", 1, publications)
            self.assertEqual(payload["sources"][0]["url"], "/pdf/paper")
            self.assertTrue(payload["sources"][0]["local_pdf"])

    def test_live_http_interface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "paper.pdf"
            pdf_bytes = b"%PDF-1.4\nlocal test"
            pdf_path.write_bytes(pdf_bytes)
            publications = PublicationFiles(
                {"research-papers/extracted/paper.md": "paper"},
                {"paper": pdf_path},
            )
            server: ThreadingHTTPServer = create_server(
                self.index, port=0, publications=publications
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(f"{base_url}/", timeout=2) as response:
                    page = response.read().decode("utf-8")
                    self.assertIn("MAL Research RAG", page)
                    self.assertIn("textContent", page)
                with urlopen(f"{base_url}/api/query?q=attack%20techniques&limit=1", timeout=2) as response:
                    payload = json.loads(response.read())
                    self.assertEqual(payload["sources"][0]["page"], 4)
                    self.assertEqual(payload["sources"][0]["url"], "/pdf/paper")
                    self.assertTrue(payload["sources"][0]["local_pdf"])
                with urlopen(f"{base_url}/pdf/paper", timeout=2) as response:
                    self.assertEqual(response.headers.get_content_type(), "application/pdf")
                    self.assertEqual(response.read(), pdf_bytes)
                with self.assertRaises(HTTPError) as error:
                    urlopen(f"{base_url}/pdf/not-allowlisted", timeout=2)
                self.assertEqual(error.exception.code, 404)
                error.exception.close()
                with self.assertRaises(HTTPError) as error:
                    urlopen(f"{base_url}/api/query", timeout=2)
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
