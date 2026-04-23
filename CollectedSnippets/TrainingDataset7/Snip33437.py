def test_basic_syntax32(self):
        output = self.engine.render_to_string(
            "basic-syntax32",
            {"1": (("x", "x", "x", "x"), ("y", "y", "y", "y"), ("a", "b", "c", "d"))},
        )
        self.assertEqual(output, "d")