def test_cut02(self):
        output = self.engine.render_to_string(
            "cut02", {"a": "x&y", "b": mark_safe("x&amp;y")}
        )
        self.assertEqual(output, "&amp;y &amp;y")