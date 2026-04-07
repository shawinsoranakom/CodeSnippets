def test_basic_syntax31(self):
        output = self.engine.render_to_string(
            "basic-syntax31",
            {"1": {"2": ("a", "b", "c", "d")}},
        )
        self.assertEqual(output, "d")