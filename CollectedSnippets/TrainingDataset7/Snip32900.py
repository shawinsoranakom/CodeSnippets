def test_escape01(self):
        output = self.engine.render_to_string(
            "escape01", {"a": "x&y", "b": mark_safe("x&y")}
        )
        self.assertEqual(output, "x&amp;y x&y")