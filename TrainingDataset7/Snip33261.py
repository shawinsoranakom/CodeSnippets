def test_wrap_long_text(self):
        long_text = (
            "this is a long paragraph of text that really needs"
            " to be wrapped I'm afraid " * 20_000
        )
        self.assertIn(
            "this is a\nlong\nparagraph\nof text\nthat\nreally\nneeds to\nbe wrapped\n"
            "I'm afraid",
            wordwrap(long_text, 10),
        )