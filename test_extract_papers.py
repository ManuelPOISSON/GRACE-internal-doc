import unittest

from extract_papers import _add_markdown_subheadings, _detect_numbered_headings


class ExtractPaperTests(unittest.TestCase):
    def test_detects_sections_but_rejects_numbered_prose(self) -> None:
        pages = [
            "1. Introduction\nOpening text.",
            "2. Methodology\n2.1. Setup\n6. We already know how the flags are arranged.",
            "3. Results\n"
            "4. Enable non-security expert for analysis. The security analysis\n"
            "3.1. Comparison\n"
            "4. Conclusion\n"
            "Acknowledgments",
        ]
        headings = _detect_numbered_headings(pages)
        self.assertEqual(
            headings,
            {
                "1. Introduction",
                "2. Methodology",
                "2.1. Setup",
                "3. Results",
                "3.1. Comparison",
                "4. Conclusion",
            },
        )
        markdown = _add_markdown_subheadings(pages[1], headings)
        self.assertIn("### 2. Methodology", markdown)
        self.assertIn("#### 2.1. Setup", markdown)
        self.assertIn("6. We already know", markdown)
        self.assertNotIn("### 6. We already know", markdown)


if __name__ == "__main__":
    unittest.main()
