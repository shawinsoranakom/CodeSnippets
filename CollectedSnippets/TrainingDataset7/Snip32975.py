def test_last01(self):
        output = self.engine.render_to_string(
            "last01", {"a": ["x", "a&b"], "b": ["x", mark_safe("a&b")]}
        )
        self.assertEqual(output, "a&amp;b a&b")