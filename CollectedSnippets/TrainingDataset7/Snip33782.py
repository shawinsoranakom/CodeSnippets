def test_ifchanged06(self):
        output = self.engine.render_to_string(
            "ifchanged06", {"num": (1, 1, 1), "numx": (2, 2, 2)}
        )
        self.assertEqual(output, "1222")