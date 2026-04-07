def test_ifchanged_param02(self):
        output = self.engine.render_to_string(
            "ifchanged-param02", {"num": (1, 2, 3), "numx": (5, 6, 7)}
        )
        self.assertEqual(output, "..567..567..567")