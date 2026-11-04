# MAL RAG

This project indexes authoritative material from the [Meta Attack Language (MAL)](https://mal-lang.org/) ecosystem and provides local tools for retrieval and editing research diagrams.

## Setup

The `mal-lang` repositories that the RAG indexes are not stored in this repository. Before using the RAG, run the fetch script once from the project root (it needs `git` and network access), then build the index:

```bash
./fetchSources.sh
python3 mal_rag.py build
```

`fetchSources.sh` clones the seven public `mal-lang` repositories into `sources/` and updates them if they already exist. Run it again whenever you want fresh sources, then rebuild the index. Research paper PDFs are not distributed; the catalog and extracted text are already in `sources/research-papers/`.

## Documentation

- [MAL RAG command line and web interface](docs/rag.md) — use `mal_rag.py` and `rag_web.py`.
- [Editable research mind map](docs/mindmap.md) — use `mindmap_web.py`.
- [Editable pipeline graph](docs/pipeline.md) — use `pipeline_web.py`.

Each guide explains how to use the tool and lists its arguments and options.

