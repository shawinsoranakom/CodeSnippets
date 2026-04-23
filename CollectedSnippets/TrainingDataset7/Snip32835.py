def test_chaining02(self):
        output = self.engine.render_to_string(
            "chaining02", {"a": "a < b", "b": mark_safe("a < b")}
        )
        self.assertEqual(output, " A < b . A < b ")