def test_cut01(self):
        output = self.engine.render_to_string(
            "cut01", {"a": "x&y", "b": mark_safe("x&amp;y")}
        )
        self.assertEqual(output, "&y &amp;y")