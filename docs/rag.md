# MAL RAG command line and web interface

Run commands from the project root with Python 3. The indexer and web server use the Python standard library.

## Quick start

```bash
python3 mal_rag.py build
python3 mal_rag.py query "How do I define an asset and an attack step?"
python3 rag_web.py
```

Open the URL printed by `rag_web.py` (normally <http://127.0.0.1:8000>). Build the index before starting the web server. Stop the server with Control-C. Run `python3 -m unittest -v` to run the project tests.

## `mal_rag.py` arguments

| Command or argument | Default | Purpose |
| --- | --- | --- |
| `build` | — | Build a JSON index from source files. |
| `build --sources PATH` | `sources` | Source directory to index, relative to the current directory unless absolute. |
| `build --output PATH` | `data/index.json` | Destination index file; the parent directory is created if needed. |
| `query TEXT` | Required | Search text; quote it when it contains spaces. |
| `query --index PATH` | `data/index.json` | Index file to read. |
| `query --limit N` | `5` | Maximum number of retrieved matches. |
| `-h`, `--help` | — | Show help for the script or a subcommand. |

```bash
python3 mal_rag.py build --sources sources --output data/index.json
python3 mal_rag.py query "How can MAL attack simulations be applied to BPMN?" --limit 3
```

The default corpus is `sources/`. The index stores each chunk's repository, path, section title, kind, and text. Retrieval uses TF-IDF-style lexical ranking with phrase and MAL-term boosts. Query output ends in `Sources:` so you can verify the original material. Programmatic callers can use `Index.answer(...)` to get a `RagAnswer` with structured `Citation` objects, including repository, source path, score, and available paper page and publication links.

## `rag_web.py` arguments and options

| Argument | Default | Purpose |
| --- | --- | --- |
| `--index PATH` | `data/index.json` beside the script | Index file to load. |
| `--catalog PATH` | `sources/research-papers/catalog.json` beside the script | Catalog for local PDFs and publication links. |
| `--host HOST` | `127.0.0.1` | Address to bind the server to. |
| `--port PORT` | `8000` | TCP port for the web interface. |
| `-h`, `--help` | — | Show command line help. |

```bash
python3 rag_web.py --index data/index.json --catalog sources/research-papers/catalog.json --port 8000
```

Enter a question in the browser to see retrieved text and citations. Results show source path, score, and available PDF page and subsection. **Open publication** opens a local cataloged PDF when available, otherwise a DOI or publisher URL. The web server exposes `GET /api/health`, `GET /api/query?q=TEXT&limit=N`, and `GET /pdf/PAPER_ID`. The query is required and limited to 500 characters; `limit` defaults to 5 and must be an integer from 1 to 10.

## Research papers and corpus

The included `sources/` directory contains public material from the official `mal-lang` GitHub organization:

| Directory | Content |
| --- | --- |
| `mal-specification-wiki` | Normative MAL specification pages. |
| `malcompiler` | Grammar, compiler behavior, and tests. |
| `mal-toolbox` | APIs and integration examples. |
| `mal-tutorials` | Guided language and model tutorials. |
| `exampleLang` | A minimal working MAL language. |
| `mal-lang.github.io` | Ecosystem documentation and website content. |
| `research-papers` | Downloaded MAL research, page-aware extracts, and catalog. |

Original research PDFs live in `sources/research-papers/pdfs/`, with provenance in `catalog.json`. `extract_papers.py` creates reading-order, page-marked Markdown and a checksum manifest. Papers configured with `raw_with_headings` are also split into sections and subsections. PDF text is dehyphenated and chunked at paragraph or sentence boundaries; displayed paper matches use short complete-sentence windows. Paper chunks carry page and DOI metadata when available.

To re-extract papers and rebuild the index:

```bash
python3 extract_papers.py
python3 mal_rag.py build
```

Refresh the source repositories as needed before rebuilding. Check any generated MAL with the MAL compiler or toolbox before using it.
