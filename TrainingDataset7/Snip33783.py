def test_ifchanged07(self):
        output = self.engine.render_to_string(
            "ifchanged07", {"num": (1, 1, 1), "numx": (2, 2, 2), "numy": (3, 3, 3)}
        )
        self.assertEqual(output, "1233323332333")