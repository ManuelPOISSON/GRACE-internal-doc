"""Extract downloaded MAL research PDFs into page-aware RAG documents."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import TypedDict


ROOT = Path(__file__).parent
PAPER_ROOT = ROOT / "sources" / "research-papers"
CATALOG = PAPER_ROOT / "catalog.json"
NUMBERED_HEADING_RE: re.Pattern[str] = re.compile(
    r"^(?P<number>(?:[1-9]|[1-9]\d?)(?:\.\d+)*\.)\s+"
    r"(?P<title>[^\n]{2,58}?)\s*$"
)
UNNUMBERED_HEADINGS: frozenset[str] = frozenset({
    "Acknowledgments",
    "CRediT authorship contribution statement",
    "Declaration of competing interest",
    "Data availability",
    "References",
})


class PaperRecord(TypedDict, total=False):
    id: str
    title: str
    authors: list[str]
    year: int
    doi: str
    source_url: str
    pdf: str
    extraction_mode: str
    availability_note: str
    status: str
    pages: int
    sha256: str


class CatalogRecord(TypedDict):
    source: str
    source_url: str
    papers: list[PaperRecord]


def _extract_pages(pdf: Path, extraction_mode: str = "layout") -> list[str]:
    text_mode = "-layout" if extraction_mode == "layout" else "-raw"
    result = subprocess.run(
        ["pdftotext", text_mode, str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [page.strip() for page in result.stdout.split("\f") if page.strip()]


def _detect_numbered_headings(pages: list[str]) -> set[str]:
    """Keep section numbering while rejecting numbered prose/list items."""
    headings: set[str] = set()
    current_top_level = 0
    for page in pages:
        for line in page.splitlines():
            stripped = line.strip()
            match = NUMBERED_HEADING_RE.fullmatch(stripped)
            if not match:
                continue
            components = [int(part) for part in match.group("number").rstrip(".").split(".")]
            if len(components) == 1:
                if components[0] != current_top_level + 1:
                    continue
                current_top_level = components[0]
                headings.add(stripped)
            elif components[0] == current_top_level:
                headings.add(stripped)
    return headings


def _add_markdown_subheadings(
    text: str,
    numbered_headings: AbstractSet[str] | None = None,
) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        numbered = NUMBERED_HEADING_RE.fullmatch(stripped)
        if numbered and (numbered_headings is None or stripped in numbered_headings):
            number = numbered.group("number")
            level = min(2 + number.count("."), 6)
            lines.append(f"{'#' * level} {number} {numbered.group('title')}")
        elif stripped in UNNUMBERED_HEADINGS or stripped.startswith("Appendix "):
            lines.append(f"### {stripped}")
        else:
            lines.append(line.rstrip())
    return "\n".join(lines).strip()


def extract() -> list[PaperRecord]:
    catalog: CatalogRecord = json.loads(CATALOG.read_text(encoding="utf-8"))
    output_dir = PAPER_ROOT / "extracted"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[PaperRecord] = []
    for paper in catalog["papers"]:
        pdf_name = paper.get("pdf")
        if not pdf_name:
            entry = paper.copy()
            entry["status"] = "metadata_only"
            manifest.append(entry)
            continue
        pdf = PAPER_ROOT / "pdfs" / pdf_name
        if not pdf.exists():
            entry = paper.copy()
            entry["status"] = "download_unavailable"
            manifest.append(entry)
            continue
        extraction_mode = paper.get("extraction_mode", "raw")
        pages = _extract_pages(pdf, extraction_mode)
        if extraction_mode == "raw_with_headings":
            numbered_headings = _detect_numbered_headings(pages)
            pages = [
                _add_markdown_subheadings(page, numbered_headings)
                for page in pages
            ]
        sha256 = hashlib.sha256(pdf.read_bytes()).hexdigest()
        frontmatter: dict[str, str] = {
            "document_type": "research_paper",
            "paper_id": paper["id"],
            "title": paper["title"],
            "authors": "; ".join(paper.get("authors", [])),
            "year": str(paper.get("year", "")),
            "doi": paper.get("doi", ""),
            "source_url": paper["source_url"],
            "pdf": f"../pdfs/{pdf.name}",
            "extraction_mode": extraction_mode,
            "sha256": sha256,
            "pages": str(len(pages)),
        }
        lines = ["---", *[f"{key}: {value}" for key, value in frontmatter.items()], "---", ""]
        for page_number, page in enumerate(pages, 1):
            lines.extend([f"## Page {page_number}", "", page, ""])
        output = output_dir / f"{paper['id']}.md"
        output.write_text("\n".join(lines), encoding="utf-8")
        entry = paper.copy()
        entry.update({"status": "extracted", "pages": len(pages), "sha256": sha256})
        manifest.append(entry)
    (PAPER_ROOT / "manifest.json").write_text(
        json.dumps({"papers": manifest}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    records = extract()
    extracted = sum(item["status"] == "extracted" for item in records)
    print(f"Extracted {extracted} of {len(records)} catalogued MAL papers")
