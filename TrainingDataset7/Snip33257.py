def test_indent(self):
        self.assertEqual(
            wordwrap(
                "this is a short paragraph of text.\n  But this line should be "
                "indented",
                14,
            ),
            "this is a\nshort\nparagraph of\ntext.\n  But this\nline should be\n"
            "indented",
        )