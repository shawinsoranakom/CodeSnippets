def test_random02(self):
        output = self.engine.render_to_string(
            "random02", {"a": ["a&b", "a&b"], "b": [mark_safe("a&b"), mark_safe("a&b")]}
        )
        self.assertEqual(output, "a&b a&b")