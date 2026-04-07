def test_colorize_empty_text(self):
        self.assertEqual(colorize(text=None), "\x1b[m\x1b[0m")
        self.assertEqual(colorize(text=""), "\x1b[m\x1b[0m")

        self.assertEqual(colorize(text=None, opts=("noreset",)), "\x1b[m")
        self.assertEqual(colorize(text="", opts=("noreset",)), "\x1b[m")