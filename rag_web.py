"""Small dependency-free web interface for querying the MAL RAG."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TypedDict, cast
from urllib.parse import parse_qs, quote, unquote, urlparse

from mal_rag import Citation, Index, IndexRecord


ROOT = Path(__file__).resolve().parent
DEFAULT_INDEX = ROOT / "data" / "index.json"
DEFAULT_CATALOG = ROOT / "sources" / "research-papers" / "catalog.json"
MAX_QUERY_LENGTH = 500
MAX_LIMIT = 10


class SourcePayload(TypedDict):
    rank: int
    title: str
    source: str
    repository: str
    kind: str
    score: float
    page: int | None
    section: str | None
    url: str | None
    local_pdf: bool


class QueryPayload(TypedDict):
    query: str
    answer: str
    sources: list[SourcePayload]


@dataclass(frozen=True)
class PublicationFiles:
    """Allowlisted local PDFs, indexed by extracted source and paper ID."""

    paper_id_by_source: Mapping[str, str]
    pdf_by_paper_id: Mapping[str, Path]

    @classmethod
    def empty(cls) -> PublicationFiles:
        return cls({}, {})

    def local_url(self, source: str) -> str | None:
        paper_id = self.paper_id_by_source.get(source)
        return f"/pdf/{quote(paper_id, safe='')}" if paper_id else None


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MAL Research RAG</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17202a;
      --muted: #5f6b76;
      --paper: #fffdf8;
      --panel: #ffffff;
      --line: #d8dde3;
      --accent: #0b6b5b;
      --accent-dark: #074c41;
      --soft: #e9f4f1;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #dcefea 0, transparent 32rem),
        var(--paper);
    }
    main { width: min(940px, calc(100% - 2rem)); margin: 0 auto; padding: 4rem 0; }
    header { margin-bottom: 2rem; }
    .eyebrow { color: var(--accent); font-weight: 750; letter-spacing: .08em; text-transform: uppercase; }
    h1 { margin: .35rem 0 .6rem; font-family: Georgia, serif; font-size: clamp(2.2rem, 6vw, 4.6rem); line-height: .98; }
    .intro { max-width: 720px; color: var(--muted); font-size: 1.05rem; line-height: 1.6; }
    form {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: .7rem;
      padding: .75rem;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255,255,255,.9);
      box-shadow: 0 18px 50px rgba(26, 57, 50, .09);
    }
    input, button { font: inherit; }
    input {
      min-width: 0;
      padding: .95rem 1rem;
      border: 1px solid var(--line);
      border-radius: 10px;
      color: var(--ink);
      background: #fff;
    }
    input:focus { outline: 3px solid #a7d7cc; border-color: var(--accent); }
    button {
      border: 0;
      border-radius: 10px;
      padding: .95rem 1.3rem;
      color: white;
      background: var(--accent);
      font-weight: 750;
      cursor: pointer;
    }
    button:hover { background: var(--accent-dark); }
    button:disabled { cursor: wait; opacity: .62; }
    #status { min-height: 1.5rem; margin: 1.2rem .2rem; color: var(--muted); }
    .panel { margin-top: 1rem; padding: 1.25rem; border: 1px solid var(--line); border-radius: 14px; background: var(--panel); }
    .panel h2 { margin-top: 0; font-family: Georgia, serif; }
    pre { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; font: 0.94rem/1.55 ui-monospace, SFMono-Regular, Menlo, monospace; }
    #sources { display: grid; gap: .8rem; padding: 0; list-style: none; }
    .source { padding: 1rem; border-left: 4px solid var(--accent); border-radius: 8px; background: var(--soft); }
    .source strong { display: block; margin-bottom: .35rem; }
    .meta { color: var(--muted); font-size: .9rem; line-height: 1.5; }
    a { color: var(--accent-dark); font-weight: 700; }
    [hidden] { display: none !important; }
    @media (max-width: 640px) {
      main { padding: 2rem 0; }
      form { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div class="eyebrow">Meta Attack Language</div>
      <h1>Research RAG</h1>
      <p class="intro">Search the local MAL repositories and research-paper corpus. Results include the exact file, PDF page, subsection, and publication link whenever available.</p>
    </header>
    <form id="query-form">
      <label for="query" hidden>Question</label>
      <input id="query" name="query" aria-label="Question" maxlength="500" required autofocus placeholder="How was coreLang validated against MITRE ATT&amp;CK?">
      <button id="submit" type="submit">Search</button>
    </form>
    <p id="status" role="status" aria-live="polite">Ready.</p>
    <section id="answer-panel" class="panel" hidden>
      <h2>Retrieved answer</h2>
      <pre id="answer"></pre>
    </section>
    <section id="sources-panel" class="panel" hidden>
      <h2>Sources</h2>
      <ol id="sources"></ol>
    </section>
  </main>
  <script>
    const form = document.querySelector('#query-form');
    const input = document.querySelector('#query');
    const submit = document.querySelector('#submit');
    const status = document.querySelector('#status');
    const answerPanel = document.querySelector('#answer-panel');
    const sourcesPanel = document.querySelector('#sources-panel');
    const answerNode = document.querySelector('#answer');
    const sourcesNode = document.querySelector('#sources');

    function sourceCard(source) {
      const item = document.createElement('li');
      item.className = 'source';
      const title = document.createElement('strong');
      title.textContent = `[${source.rank}] ${source.title}`;
      const meta = document.createElement('div');
      meta.className = 'meta';
      const details = [source.source];
      if (source.page !== null) details.push(`page ${source.page}`);
      if (source.section) details.push(`section ${source.section}`);
      details.push(`score ${source.score.toFixed(3)}`);
      meta.textContent = details.join(' · ');
      item.append(title, meta);
      if (source.url) {
        const link = document.createElement('a');
        link.href = source.url;
        link.target = '_blank';
        link.rel = 'noreferrer';
        link.textContent = source.local_pdf ? 'Open publication (local PDF)' : 'Open publication';
        item.append(document.createElement('br'), link);
      }
      return item;
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const query = input.value.trim();
      if (!query) return;
      submit.disabled = true;
      status.textContent = 'Searching the local corpus…';
      answerPanel.hidden = true;
      sourcesPanel.hidden = true;
      try {
        const response = await fetch(`/api/query?q=${encodeURIComponent(query)}&limit=5`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Query failed.');
        answerNode.textContent = data.answer;
        sourcesNode.replaceChildren(...data.sources.map(sourceCard));
        answerPanel.hidden = false;
        sourcesPanel.hidden = false;
        status.textContent = `${data.sources.length} source${data.sources.length === 1 ? '' : 's'} retrieved.`;
      } catch (error) {
        status.textContent = error.message;
      } finally {
        submit.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


def citation_url(
    citation: Citation,
    publications: PublicationFiles | None = None,
) -> tuple[str | None, bool]:
    local_url = publications.local_url(citation.source) if publications else None
    if local_url:
        return local_url, True
    if citation.doi:
        return f"https://doi.org/{citation.doi}", False
    return citation.source_url, False


def query_payload(
    index: Index,
    query: str,
    limit: int = 5,
    publications: PublicationFiles | None = None,
) -> QueryPayload:
    answer = index.answer(query, limit)
    sources: list[SourcePayload] = []
    for source in answer.sources:
        url, is_local = citation_url(source, publications)
        sources.append({
            "rank": source.rank,
            "title": source.title,
            "source": source.source,
            "repository": source.repository,
            "kind": source.kind,
            "score": source.score,
            "page": source.page,
            "section": source.section,
            "url": url,
            "local_pdf": is_local,
        })
    return {"query": query, "answer": answer.text, "sources": sources}


def load_index(path: Path) -> Index:
    data = cast(IndexRecord, json.loads(path.read_text(encoding="utf-8")))
    return Index.from_dict(data)


def load_publication_files(catalog_path: Path) -> PublicationFiles:
    raw: object = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("papers"), list):
        raise ValueError(f"Invalid paper catalog: {catalog_path}")
    pdf_root = (catalog_path.parent / "pdfs").resolve()
    paper_id_by_source: dict[str, str] = {}
    pdf_by_paper_id: dict[str, Path] = {}
    for item in raw["papers"]:
        if not isinstance(item, dict):
            continue
        paper_id = item.get("id")
        pdf_name = item.get("pdf")
        if not isinstance(paper_id, str) or not isinstance(pdf_name, str):
            continue
        if Path(pdf_name).name != pdf_name or Path(pdf_name).suffix.lower() != ".pdf":
            continue
        pdf_path = (pdf_root / pdf_name).resolve()
        if pdf_path.parent != pdf_root or not pdf_path.is_file():
            continue
        source = f"research-papers/extracted/{paper_id}.md"
        paper_id_by_source[source] = paper_id
        pdf_by_paper_id[paper_id] = pdf_path
    return PublicationFiles(paper_id_by_source, pdf_by_paper_id)


def make_handler(
    index: Index,
    publications: PublicationFiles | None = None,
) -> type[BaseHTTPRequestHandler]:
    publication_files = publications or PublicationFiles.empty()

    class RagHandler(BaseHTTPRequestHandler):
        def _send_bytes(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: HTTPStatus, payload: object) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(status, "application/json; charset=utf-8", body)

        def do_GET(self) -> None:
            request = urlparse(self.path)
            if request.path == "/":
                self._send_bytes(HTTPStatus.OK, "text/html; charset=utf-8", HTML.encode("utf-8"))
                return
            if request.path == "/api/health":
                self._send_json(HTTPStatus.OK, {"status": "ok", "chunks": len(index.chunks)})
                return
            if request.path.startswith("/pdf/"):
                paper_id = unquote(request.path.removeprefix("/pdf/"))
                pdf_path = publication_files.pdf_by_paper_id.get(paper_id)
                if pdf_path is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "Local PDF not found."})
                    return
                self._send_bytes(HTTPStatus.OK, "application/pdf", pdf_path.read_bytes())
                return
            if request.path != "/api/query":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
                return
            parameters = parse_qs(request.query)
            query = parameters.get("q", [""])[0].strip()
            if not query:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Query parameter 'q' is required."})
                return
            if len(query) > MAX_QUERY_LENGTH:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Query is too long."})
                return
            try:
                limit = int(parameters.get("limit", ["5"])[0])
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Limit must be an integer."})
                return
            if not 1 <= limit <= MAX_LIMIT:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"Limit must be between 1 and {MAX_LIMIT}."})
                return
            self._send_json(
                HTTPStatus.OK,
                query_payload(index, query, limit, publication_files),
            )

        def log_message(self, format_string: str, *args: object) -> None:
            return

    return RagHandler


def create_server(
    index: Index,
    host: str = "127.0.0.1",
    port: int = 8000,
    publications: PublicationFiles | None = None,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(index, publications))


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the local MAL RAG web interface.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args: argparse.Namespace = parser.parse_args()
    index = load_index(args.index)
    publications = load_publication_files(args.catalog)
    server = create_server(index, args.host, args.port, publications)
    print(f"MAL RAG web interface: http://{args.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
