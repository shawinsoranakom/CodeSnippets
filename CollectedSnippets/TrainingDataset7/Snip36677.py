def test_colorize_reset(self):
        self.assertEqual(colorize(text="", opts=("reset",)), "\x1b[0m")