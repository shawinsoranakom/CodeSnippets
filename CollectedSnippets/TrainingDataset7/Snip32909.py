def test_backslashes(self):
        self.assertEqual(
            escapejs_filter(r"\ : backslashes, too"), "\\u005C : backslashes, too"
        )