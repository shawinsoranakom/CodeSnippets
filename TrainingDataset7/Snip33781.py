def test_ifchanged05(self):
        output = self.engine.render_to_string(
            "ifchanged05", {"num": (1, 1, 1), "numx": (1, 2, 3)}
        )
        self.assertEqual(output, "1123123123")