import json
import tempfile
import unittest
from pathlib import Path
from typing import get_type_hints

from mal_rag import Chunk, Index, _bounded_text_chunks, _paper_excerpt, build_index, collect_chunks


class MalRagTests(unittest.TestCase):
    def test_collects_markdown_and_mal_with_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "repo").mkdir()
            (root / "repo" / "guide.md").write_text("# Assets\nAssets define modeled entities.", encoding="utf-8")
            (root / "repo" / "language.mal").write_text("asset Host { compromise: attack; }", encoding="utf-8")
            chunks = collect_chunks(root)
            self.assertEqual(len(chunks), 2)
            self.assertEqual({chunk.kind for chunk in chunks}, {"md", "mal"})
            self.assertTrue(all(chunk.repository == "repo" for chunk in chunks))

    def test_search_prefers_exact_mal_concept(self):
        index = Index([
            Chunk("one", "guide.md", "repo", "Assets", "Assets represent entities.", "md"),
            Chunk("two", "lang.mal", "repo", "Language", "asset Host { compromise: attack; }", "mal"),
        ])
        matches = index.search("asset attack", limit=1)
        self.assertEqual(matches[0][1].id, "two")
        self.assertIn("lang.mal", index.context("asset attack"))

    def test_build_writes_loadable_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "sources"
            root.mkdir()
            (root / "doc.md").write_text("# MAL\nAn attack step reaches an asset.", encoding="utf-8")
            output = Path(directory) / "data" / "index.json"
            self.assertEqual(build_index(root, output), 1)
            self.assertEqual(len(Index.from_dict(json.loads(output.read_text())).chunks), 1)

    def test_collects_page_aware_research_paper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paper_dir = root / "research-papers" / "extracted"
            paper_dir.mkdir(parents=True)
            (paper_dir / "paper.md").write_text(
                "---\ndocument_type: research_paper\ntitle: Formal MAL\n"
                "year: 2023\ndoi: 10.1000/mal\n---\n\n"
                "## Page 1\n\nAssets and attack steps.\n\n"
                "## Page 2\n\n### 4. Validation\n\nDefenses and associations.\n",
                encoding="utf-8",
            )
            chunks = collect_chunks(root)
            self.assertEqual([chunk.page for chunk in chunks], [1, 2])
            self.assertTrue(all(chunk.kind == "paper" for chunk in chunks))
            self.assertTrue(all(chunk.doi == "10.1000/mal" for chunk in chunks))
            self.assertEqual(chunks[1].section, "4. Validation")
            self.assertIn("4. Validation", chunks[1].title)
            self.assertIn("page 2, DOI 10.1000/mal", Index(chunks).context("associations"))

    def test_answer_always_exposes_structured_sources(self):
        index = Index([
            Chunk(
                "paper:1",
                "research-papers/extracted/formal-mal.md",
                "research-papers",
                "Formal MAL — page 2",
                "Associations connect assets.",
                "paper",
                page=2,
                doi="10.1000/mal",
                source_url="https://example.test/paper",
            )
        ])
        answer = index.answer("associations")
        self.assertEqual(len(answer.sources), 1)
        self.assertEqual(answer.sources[0].page, 2)
        self.assertIn("https://doi.org/10.1000/mal", answer.format())
        self.assertIn("Sources:", index.context("associations"))
        self.assertEqual(Index([]).answer("missing").sources, ())
        self.assertIn("Sources:\n- None", Index([]).context("missing"))

    def test_answer_uses_publication_url_when_doi_is_absent(self):
        index = Index([
            Chunk(
                "paper:2",
                "research-papers/extracted/arxiv-paper.md",
                "research-papers",
                "ArXiv MAL Paper — page 1",
                "A simulator based on attack graphs.",
                "paper",
                page=1,
                source_url="https://arxiv.org/abs/2609.16563",
            )
        ])
        answer = index.answer("simulator attack graphs")
        self.assertEqual(answer.sources[0].source_url, "https://arxiv.org/abs/2609.16563")
        self.assertIn("https://arxiv.org/abs/2609.16563", answer.format())

    def test_search_prefers_matching_subheading(self):
        index = Index([
            Chunk(
                "page-intro",
                "paper.md",
                "research-papers",
                "Paper — page 5",
                "The process of validation against MITRE ATT&CK is discussed later.",
                "paper",
                page=5,
            ),
            Chunk(
                "section",
                "paper.md",
                "research-papers",
                "Paper — 3.1. Process of validation against MITRE ATT&CK (page 5)",
                "### 3.1. Process of validation against MITRE ATT&CK\nMethod details.",
                "paper",
                page=5,
                section="3.1. Process of validation against MITRE ATT&CK",
            ),
        ])
        match = index.search("Process of validation against MITRE ATT&CK", limit=1)[0][1]
        self.assertEqual(match.id, "section")

    def test_chunking_uses_complete_sentence_boundaries(self) -> None:
        text = (
            "The first sentence explains the modeled asset. "
            "The second sentence explains the attack path in detail. "
            "The third sentence explains the defense."
        )
        chunks = _bounded_text_chunks(text, max_chars=80)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.endswith((".", "!", "?")) for chunk in chunks))
        self.assertTrue(all(chunk[:1].isupper() for chunk in chunks))

    def test_paper_excerpt_removes_incomplete_page_fragment(self) -> None:
        text = (
            "A Paper (2024)\n\n"
            "differentiation continued from the previous page. "
            "Attack simulations identify complete attack paths. "
            "The resulting paths help security engineers prioritize defenses."
        )
        excerpt = _paper_excerpt(text, "attack simulations")
        self.assertNotIn("differentiation continued", excerpt)
        self.assertIn("Attack simulations identify complete attack paths.", excerpt)
        self.assertLess(
            excerpt.index("Attack simulations"),
            excerpt.index("resulting paths"),
        )
        self.assertTrue(excerpt.endswith("."))

    def test_public_rag_api_has_type_hints(self):
        for callable_object in (
            collect_chunks,
            build_index,
            Index.__init__,
            Index.search,
            Index.answer,
            Index.context,
            Index.to_dict,
            Index.from_dict,
        ):
            hints = get_type_hints(callable_object)
            self.assertIn("return", hints)


if __name__ == "__main__":
    unittest.main()
