def test_wrap_preserve_whitespace(self):
        width = 5
        width_spaces = " " * width
        cases = [
            (
                f"first line\n{width_spaces}\nsecond line",
                f"first\nline\n{width_spaces}\nsecond\nline",
            ),
            (
                "first line\n \t\t\t \nsecond line",
                "first\nline\n \t\t\t \nsecond\nline",
            ),
            (
                f"first line\n{width_spaces}\nsecond line\n\nthird{width_spaces}\n",
                f"first\nline\n{width_spaces}\nsecond\nline\n\nthird\n",
            ),
            (
                f"first line\n{width_spaces}{width_spaces}\nsecond line",
                f"first\nline\n{width_spaces}{width_spaces}\nsecond\nline",
            ),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(wordwrap(text, width), expected)