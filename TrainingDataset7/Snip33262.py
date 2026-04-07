def test_wrap_preserve_newlines(self):
        cases = [
            (
                "this is a long paragraph of text that really needs to be wrapped\n\n"
                "that is followed by another paragraph separated by an empty line\n",
                "this is a long paragraph of\ntext that really needs to be\nwrapped\n\n"
                "that is followed by another\nparagraph separated by an\nempty line\n",
                30,
            ),
            ("\n\n\n", "\n\n\n", 5),
            ("\n\n\n\n\n\n", "\n\n\n\n\n\n", 5),
        ]
        for text, expected, width in cases:
            with self.subTest(text=text):
                self.assertEqual(wordwrap(text, width), expected)