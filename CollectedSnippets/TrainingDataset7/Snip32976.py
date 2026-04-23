def test_last02(self):
        output = self.engine.render_to_string(
            "last02", {"a": ["x", "a&b"], "b": ["x", mark_safe("a&b")]}
        )
        self.assertEqual(output, "a&b a&b")