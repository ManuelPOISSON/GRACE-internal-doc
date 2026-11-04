# Editable B1 pipeline graph

Run the local editor from the project root with Python 3:

```bash
python3 pipeline_web.py
```

Open the printed URL, normally <http://127.0.0.1:8002>. The editor reads and saves `research_plan/b1_pipeline.json` and serves `research_plan/b1_pipeline.html`. Stop the server with Control-C.

Use **Open JSON** to browse for another pipeline graph in your file explorer. **Save** replaces the selected JSON file directly. In browsers without direct file access, the local pipeline server opens the file chooser and writes to the selected file. **Use default graph** returns to the server graph selected by `--graph`. The editor asks before discarding unsaved changes when switching files.

## Command line arguments

| Argument | Default | Purpose |
| --- | --- | --- |
| `--graph PATH` | `research_plan/b1_pipeline.json` beside the script | JSON graph to load and save; it must exist and be valid at startup. |
| `--host HOST` | `127.0.0.1` | Address to bind the server to. |
| `--port PORT` | `8002` | TCP port for the editor. |
| `-h`, `--help` | — | Show command line help. |

```bash
python3 pipeline_web.py --graph research_plan/b1_pipeline.json --port 8002
```

## Editor options

- **+ Node** adds a node. Select it to edit its title, type (`file`, `data`, `agent`, `deterministic`, or `prompt`), role, relative file path, description, color, and details (one per line). Drag to move it and use its resize handle to adjust its size.
- **+ Arrow** starts a connection: select a source node, then a target node. Select an arrow to edit its label, color, solid or dashed style, and top, middle, or bottom endpoints. **Delete** or the Delete/Backspace key removes a selection.
- **Undo** and **Redo** revisit edits. **Reset zoom** fits the nodes; Control plus mouse wheel zooms. Drag the canvas background to pan. **Preview** shows a larger view; **Edit**, **Exit preview**, or Escape returns to editing.
- Set canvas width and height with the **W** and **H** controls. Width must be 400–100,000 and height 300–100,000.
- **Save** writes the server graph to the file selected by `--graph`, or replaces the JSON file chosen with **Open JSON**. The status text shows whether changes are unsaved.
- **File root** takes an absolute directory path. **Browse** selects a local folder in the browser. A node with a relative file path has an **Open file** button; it opens a selected browser file or asks the server to open the corresponding path beneath the file root. The file must exist and stay inside that root.

The graph format is version 1. It supports at most 500 nodes and 2,000 edges. The server exposes `GET /api/health`, `GET /api/pipeline`, `PUT /api/pipeline`, `POST /api/validate-pipeline`, `POST /api/browse-pipeline`, `PUT /api/selected-pipeline`, and `POST /api/open-file`. The browse endpoint uses the local desktop file chooser; the selected-pipeline endpoint writes only to the chosen file. The open-file endpoint takes JSON with absolute `root` and relative `path` values and opens the resolved local file.
