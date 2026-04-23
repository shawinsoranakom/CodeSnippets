def test_basic_syntax34(self):
        output = self.engine.render_to_string(
            "basic-syntax34", {"1": ({"x": "x"}, {"y": "y"}, {"z": "z", "3": "d"})}
        )
        self.assertEqual(output, "d")