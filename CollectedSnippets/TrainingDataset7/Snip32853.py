def test_cut06(self):
        output = self.engine.render_to_string(
            "cut06", {"a": "x&y", "b": mark_safe("x&amp;y")}
        )
        self.assertEqual(output, "x&amp;y x&amp;ampy")