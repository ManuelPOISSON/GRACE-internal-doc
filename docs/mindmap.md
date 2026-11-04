# Editable research mind map

Run the local editor from the project root with Python 3:

```bash
python3 mindmap_web.py
```

Open the printed URL, normally <http://127.0.0.1:8001>. The editor reads and saves a version 2 graph in `research_plan/research_mindmap.json`. Stop the server with Control-C.

## Command line arguments

| Argument | Default | Purpose |
| --- | --- | --- |
| `--map PATH` | `research_plan/research_mindmap.json` beside the script | JSON graph to load and save; it must exist and be valid at startup. |
| `--host HOST` | `127.0.0.1` | Address to bind the server to. |
| `--port PORT` | `8001` | TCP port for the editor. |
| `-h`, `--help` | — | Show command line help. |

```bash
python3 mindmap_web.py --map research_plan/research_mindmap.json --port 8001
```

## Editor options

- Create an isolated idea on the canvas, or select a node and add a child from the inspector. Drag nodes to reposition them. Draw a rectangle over the canvas background to select multiple nodes, then drag one selected node to move the group.
- Edit a selected node's label, notes, color, and bold text in the inspector. Copy and paste it with the inspector buttons or Control-C and Control-V; the copy gets a new ID and no edges.
- Choose a new edge's **relation** or **hierarchy** type and color, then drag the round connection handle on one node to another. Clicking the handle without dragging selects the node. Select an edge to change its type or color, or delete it. Hierarchy edges are solid; relation edges are dashed. Cycles are supported.
- Collapse a hierarchy branch from its node or inspector when its root is outside a cycle. The canvas controls can collapse all trees or show all nodes.
- Use the zoom slider, **Fit** control, or Control plus mouse wheel to adjust the view. Use **Undo** and **Redo** to revisit edits.
- Export the graph as JSON or a Mermaid flowchart, then download it from the export dialog. Use **Save** to write changes to the selected map file.

Version 1 tree data is migrated automatically to the version 2 graph without changing stable node IDs. The server offers `GET /api/health`, `GET /api/mindmap`, and `PUT /api/mindmap` for loading and saving JSON. A graph may contain at most 500 nodes and 2,000 edges; node labels are limited to 300 characters and notes to 2,000 characters.
