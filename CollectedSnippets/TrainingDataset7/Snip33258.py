def test_indent2(self):
        self.assertEqual(
            wordwrap(
                "this is a short paragraph of text.\n  But this line should be "
                "indented",
                15,
            ),
            "this is a short\nparagraph of\ntext.\n  But this line\nshould be\n"
            "indented",
        )