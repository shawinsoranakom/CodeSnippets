def test_cut05(self):
        output = self.engine.render_to_string(
            "cut05", {"a": "x&y", "b": mark_safe("x&amp;y")}
        )
        self.assertEqual(output, "x&y x&ampy")