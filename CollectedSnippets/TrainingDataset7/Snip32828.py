def test_center02(self):
        output = self.engine.render_to_string(
            "center02", {"a": "a&b", "b": mark_safe("a&b")}
        )
        self.assertEqual(output, ". a&amp;b . . a&b .")