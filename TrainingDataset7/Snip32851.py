def test_cut04(self):
        output = self.engine.render_to_string(
            "cut04", {"a": "x&y", "b": mark_safe("x&amp;y")}
        )
        self.assertEqual(output, "xy xamp;y")