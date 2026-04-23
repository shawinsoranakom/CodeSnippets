def test_ifchanged01(self):
        output = self.engine.render_to_string("ifchanged01", {"num": (1, 2, 3)})
        self.assertEqual(output, "123")