def test_chaining01(self):
        output = self.engine.render_to_string(
            "chaining01", {"a": "a < b", "b": mark_safe("a < b")}
        )
        self.assertEqual(output, " A &lt; b . A < b ")