def test_escape02(self):
        output = self.engine.render_to_string(
            "escape02", {"a": "x&y", "b": mark_safe("x&y")}
        )
        self.assertEqual(output, "x&amp;y x&y")