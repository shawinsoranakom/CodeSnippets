def test_rjust02(self):
        output = self.engine.render_to_string(
            "rjust02", {"a": "a&b", "b": mark_safe("a&b")}
        )
        self.assertEqual(output, ".  a&amp;b. .  a&b.")