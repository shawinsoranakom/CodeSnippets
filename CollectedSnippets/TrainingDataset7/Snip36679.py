def test_colorize_opts(self):
        self.assertEqual(
            colorize(text="Test", opts=("bold", "underscore")),
            "\x1b[1;4mTest\x1b[0m",
        )
        self.assertEqual(
            colorize(text="Test", opts=("blink",)),
            "\x1b[5mTest\x1b[0m",
        )
        # Ignored opts.
        self.assertEqual(
            colorize(text="Test", opts=("not_an_option",)),
            "\x1b[mTest\x1b[0m",
        )