def test_ifchanged04(self):
        output = self.engine.render_to_string(
            "ifchanged04", {"num": (1, 2, 3), "numx": (2, 2, 2)}
        )
        self.assertEqual(output, "122232")