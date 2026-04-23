def test_first02(self):
        output = self.engine.render_to_string(
            "first02", {"a": ["a&b", "x"], "b": [mark_safe("a&b"), "x"]}
        )
        self.assertEqual(output, "a&b a&b")