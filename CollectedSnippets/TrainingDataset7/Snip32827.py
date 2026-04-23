def test_center01(self):
        output = self.engine.render_to_string(
            "center01", {"a": "a&b", "b": mark_safe("a&b")}
        )
        self.assertEqual(output, ". a&b . . a&b .")