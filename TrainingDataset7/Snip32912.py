def test_paragraph_separator(self):
        self.assertEqual(
            escapejs_filter("paragraph separator:\u2029and line separator:\u2028"),
            "paragraph separator:\\u2029and line separator:\\u2028",
        )