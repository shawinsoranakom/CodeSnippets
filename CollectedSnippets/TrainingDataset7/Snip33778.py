def test_ifchanged02(self):
        output = self.engine.render_to_string("ifchanged02", {"num": (1, 1, 3)})
        self.assertEqual(output, "13")