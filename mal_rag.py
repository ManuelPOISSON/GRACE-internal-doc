"""Small, dependency-free retrieval layer for authoritative MAL sources."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

TOKEN_RE: re.Pattern[str] = re.compile(r"[A-Za-z_][A-Za-z0-9_.:-]*")
SUPPORTED_SUFFIXES: frozenset[str] = frozenset(
    {".md", ".mal", ".txt", ".java", ".py", ".xml", ".yml", ".yaml"}
)
SKIP_PARTS: frozenset[str] = frozenset(
    {".git", "node_modules", "target", "build", "dist", "__pycache__"}
)
MAL_TERMS: frozenset[str] = frozenset({
    "asset", "association", "attack", "attackstep", "defense", "requires",
    "reaches", "language", "include", "let", "override", "meta", "abstract",
})


@dataclass
class Chunk:
    id: str
    source: str
    repository: str
    title: str
    text: str
    kind: str
    page: int | None = None
    doi: str | None = None
    source_url: str | None = None
    section: str | None = None


class ChunkRecord(TypedDict):
    id: str
    source: str
    repository: str
    title: str
    text: str
    kind: str
    page: int | None
    doi: str | None
    source_url: str | None
    section: str | None


class IndexRecord(TypedDict):
    chunks: list[ChunkRecord]


SearchMatch = tuple[float, Chunk]


@dataclass(frozen=True)
class Citation:
    """Structured provenance for one retrieved source."""

    rank: int
    title: str
    source: str
    repository: str
    kind: str
    score: float
    page: int | None = None
    doi: str | None = None
    source_url: str | None = None
    section: str | None = None

    def location(self) -> str:
        parts: list[str] = [self.source]
        if self.page is not None:
            parts.append(f"page {self.page}")
        if self.section:
            parts.append(f"section {self.section}")
        publication_url = f"https://doi.org/{self.doi}" if self.doi else self.source_url
        if publication_url:
            parts.append(publication_url)
        return ", ".join(parts)


@dataclass(frozen=True)
class RagAnswer:
    """Retrieved answer text together with every source used to produce it."""

    query: str
    text: str
    sources: tuple[Citation, ...]

    def format(self) -> str:
        if not self.sources:
            return f"{self.text}\n\nSources:\n- None"
        source_lines: list[str] = [
            f"[{source.rank}] {source.title} — {source.location()}"
            for source in self.sources
        ]
        return f"{self.text}\n\nSources:\n" + "\n".join(source_lines)


def _clean_paper_prose(text: str) -> str:
    """Undo PDF line wrapping while retaining an optional Markdown heading."""
    heading = ""
    body = text
    heading_match = re.match(r"^(#{3,6}\s+[^\n]+)\n+", text)
    if heading_match:
        heading = heading_match.group(1).strip() + "\n\n"
        body = text[heading_match.end():]
    body = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", body)
    body = re.sub(r"\s*\n\s*", " ", body)
    body = re.sub(r"[ \t]+", " ", body).strip()
    return heading + body


def _bounded_text_chunks(text: str, max_chars: int) -> list[str]:
    """Split at paragraph or sentence boundaries, never at an arbitrary offset."""
    remaining = text.strip()
    chunks: list[str] = []
    while len(remaining) > max_chars:
        window = remaining[:max_chars + 1]
        minimum = max_chars // 2
        sentence_ends = [
            match.end()
            for match in re.finditer(r"[.!?](?:[\"')\]]*)\s+", window)
            if match.end() >= minimum
        ]
        paragraph_ends = [
            match.end()
            for match in re.finditer(r"\n\s*\n", window)
            if match.end() >= minimum
        ]
        if paragraph_ends:
            cut = paragraph_ends[-1]
        elif sentence_ends:
            cut = sentence_ends[-1]
        else:
            whitespace = window.rfind(" ", minimum)
            cut = whitespace + 1 if whitespace >= minimum else max_chars
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def _paper_excerpt(text: str, query: str, max_chars: int = 1800) -> str:
    """Return a short window of complete, query-relevant paper sentences."""
    citation, separator, content = text.partition("\n\n")
    if not separator:
        content = citation
        citation = ""
    clean = _clean_paper_prose(content)
    heading = ""
    heading_match = re.match(r"^(#{3,6}\s+[^\n]+)\n+", clean)
    if heading_match:
        heading = heading_match.group(1).strip()
        clean = clean[heading_match.end():].strip()
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(\[\"“])", clean)
        if sentence.strip()
    ]
    complete = [
        sentence
        for sentence in sentences
        if sentence[-1:] in {".", "!", "?"} and not sentence[:1].islower()
    ]
    if not complete:
        excerpt = clean[:max_chars].strip()
    else:
        query_tokens = set(tokenize(query))
        best = max(
            range(len(complete)),
            key=lambda index: len(query_tokens.intersection(tokenize(complete[index]))),
        )
        start = max(0, best - 1)
        end = best + 1
        while end < len(complete):
            candidate = " ".join(complete[start:end + 1])
            if len(candidate) > max_chars:
                break
            end += 1
        while start > 0:
            candidate = " ".join(complete[start - 1:end])
            if len(candidate) > max_chars:
                break
            start -= 1
        excerpt = " ".join(complete[start:end])
    prefix = "\n\n".join(part for part in (citation, heading) if part)
    return f"{prefix}\n\n{excerpt}".strip() if prefix else excerpt


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    return metadata, text[end + 5:]


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _title_for(text: str, path: Path, section: int) -> str:
    for line in text.splitlines():
        heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
        if heading:
            return heading.group(1).strip()
    return f"{path.name} (section {section})"


def _chunks_for_file(path: Path, root: Path, max_chars: int = 5000) -> Iterable[Chunk]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    if not text.strip():
        return
    relative = path.relative_to(root).as_posix()
    repository = relative.split("/", 1)[0]
    kind = path.suffix.lower().lstrip(".") or "text"
    metadata, body = _frontmatter(text)
    if metadata.get("document_type") == "research_paper":
        title = metadata.get("title", path.stem)
        doi = metadata.get("doi") or None
        source_url = metadata.get("source_url") or None
        citation = f"{title} ({metadata.get('year', 'n.d.')})"
        if doi:
            citation += f", DOI {doi}"
        pages = re.split(r"(?=^## Page \d+\s*$)", body, flags=re.MULTILINE)
        for page_block in pages:
            match = re.match(r"^## Page (\d+)\s*\n", page_block)
            if not match:
                continue
            page = int(match.group(1))
            page_text = page_block[match.end():].strip()
            if not page_text:
                continue
            sections = re.split(r"(?=^#{3,6}\s+)", page_text, flags=re.MULTILINE)
            for section_number, section_block in enumerate(sections, 1):
                section_block = section_block.strip()
                if not section_block:
                    continue
                heading = re.match(r"^#{3,6}\s+(.+?)\s*$", section_block, re.MULTILINE)
                section_title = heading.group(1).strip() if heading else None
                chunk_title = (
                    f"{title} — {section_title} (page {page})"
                    if section_title
                    else f"{title} — page {page}"
                )
                clean_section = _clean_paper_prose(section_block)
                for part, piece in enumerate(
                    _bounded_text_chunks(clean_section, max_chars), 1
                ):
                    yield Chunk(
                        id=f"{repository}:{relative}:p{page}:s{section_number}:{part}",
                        source=relative,
                        repository=repository,
                        title=chunk_title,
                        text=f"{citation}\n\n{piece}",
                        kind="paper",
                        page=page,
                        doi=doi,
                        source_url=source_url,
                        section=section_title,
                    )
        return
    sections = re.split(r"(?=^\s*#{1,6}\s+)", body, flags=re.MULTILINE) if path.suffix == ".md" else [body]
    section_number = 0
    for section in sections:
        section = section.strip()
        if not section:
            continue
        for piece in _bounded_text_chunks(section, max_chars):
            if piece:
                section_number += 1
                yield Chunk(
                    id=f"{repository}:{relative}:{section_number}",
                    source=relative,
                    repository=repository,
                    title=_title_for(section, path, section_number),
                    text=piece,
                    kind=kind,
                )


def collect_chunks(source_root: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        chunks.extend(_chunks_for_file(path, source_root) or [])
    return chunks


class Index:
    def __init__(self, chunks: Sequence[Chunk]) -> None:
        self.chunks: list[Chunk] = list(chunks)
        self.documents: list[Counter[str]] = [
            Counter(tokenize(chunk.text)) for chunk in self.chunks
        ]
        self.document_frequency: Counter[str] = Counter()
        for document in self.documents:
            self.document_frequency.update(document.keys())
        self.average_length: float = (
            sum(sum(document.values()) for document in self.documents) / len(self.documents)
            if self.documents else 0
        )

    def search(self, query: str, limit: int = 5) -> list[SearchMatch]:
        query_tokens = tokenize(query)
        if not query_tokens or not self.chunks:
            return []
        query_counts = Counter(query_tokens)
        results: list[SearchMatch] = []
        total = len(self.chunks)
        query_phrase = " ".join(query_tokens)
        for chunk, document in zip(self.chunks, self.documents):
            length = sum(document.values()) or 1
            score = 0.0
            title_tokens = tokenize(chunk.title)
            for token, query_frequency in query_counts.items():
                frequency = document.get(token, 0)
                if not frequency:
                    continue
                idf = math.log((total + 1) / (self.document_frequency[token] + 1)) + 1
                score += idf * (frequency / (frequency + 0.5 + 1.5 * length / (self.average_length or 1)))
                score += 0.15 * query_frequency
                if token in MAL_TERMS:
                    score += 0.1
                if token in title_tokens:
                    score += 0.25 * query_frequency
            normalized = " ".join(tokenize(chunk.text))
            if query_phrase in normalized:
                score += 1.5
            if query_phrase in " ".join(title_tokens):
                score += 2.0
            if score:
                results.append((score, chunk))
        return sorted(results, key=lambda item: (-item[0], item[1].id))[:limit]

    def answer(self, query: str, limit: int = 5) -> RagAnswer:
        matches = self.search(query, limit)
        if not matches:
            return RagAnswer(
                query=query,
                text="No matching MAL source material was found.",
                sources=(),
            )
        blocks: list[str] = []
        sources: list[Citation] = []
        for rank, (score, chunk) in enumerate(matches, 1):
            provenance = chunk.source
            if chunk.page is not None:
                provenance += f", page {chunk.page}"
            if chunk.doi:
                provenance += f", DOI {chunk.doi}"
            displayed_text = (
                _paper_excerpt(chunk.text, query) if chunk.kind == "paper" else chunk.text
            )
            blocks.append(
                f"[{rank}] {chunk.title} ({provenance}, score={score:.3f})\n{displayed_text}"
            )
            sources.append(
                Citation(
                    rank=rank,
                    title=chunk.title,
                    source=chunk.source,
                    repository=chunk.repository,
                    kind=chunk.kind,
                    score=score,
                    page=chunk.page,
                    doi=chunk.doi,
                    source_url=chunk.source_url,
                    section=chunk.section,
                )
            )
        return RagAnswer(query=query, text="\n\n".join(blocks), sources=tuple(sources))

    def context(self, query: str, limit: int = 5) -> str:
        """Return citation-ready text with an explicit source list."""
        return self.answer(query, limit).format()

    def to_dict(self) -> IndexRecord:
        return {
            "chunks": [
                {
                    "id": chunk.id,
                    "source": chunk.source,
                    "repository": chunk.repository,
                    "title": chunk.title,
                    "text": chunk.text,
                    "kind": chunk.kind,
                    "page": chunk.page,
                    "doi": chunk.doi,
                    "source_url": chunk.source_url,
                    "section": chunk.section,
                }
                for chunk in self.chunks
            ]
        }

    @classmethod
    def from_dict(cls, data: IndexRecord) -> Index:
        return cls([Chunk(**item) for item in data["chunks"]])


def build_index(source_root: Path, output: Path) -> int:
    index = Index(collect_chunks(source_root))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index.to_dict(), indent=2), encoding="utf-8")
    return len(index.chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Index and query MAL documentation.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="Build a JSON index from source repositories.")
    build.add_argument("--sources", type=Path, default=Path("sources"))
    build.add_argument("--output", type=Path, default=Path("data/index.json"))
    query = subparsers.add_parser("query", help="Retrieve source-backed MAL context.")
    query.add_argument("text")
    query.add_argument("--index", type=Path, default=Path("data/index.json"))
    query.add_argument("--limit", type=int, default=5)
    args: argparse.Namespace = parser.parse_args()
    if args.command == "build":
        print(f"Indexed {build_index(args.sources, args.output)} chunks into {args.output}")
    else:
        index = Index.from_dict(json.loads(args.index.read_text(encoding="utf-8")))
        print(index.context(args.text, args.limit))


if __name__ == "__main__":
    main()
