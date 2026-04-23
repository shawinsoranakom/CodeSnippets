def test_colorize_fg_bg(self):
        self.assertEqual(colorize(text="Test", fg="red"), "\x1b[31mTest\x1b[0m")
        self.assertEqual(colorize(text="Test", bg="red"), "\x1b[41mTest\x1b[0m")
        # Ignored kwarg.
        self.assertEqual(colorize(text="Test", other="red"), "\x1b[mTest\x1b[0m")