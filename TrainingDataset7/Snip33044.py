def test_random01(self):
        output = self.engine.render_to_string(
            "random01", {"a": ["a&b", "a&b"], "b": [mark_safe("a&b"), mark_safe("a&b")]}
        )
        self.assertEqual(output, "a&amp;b a&b")