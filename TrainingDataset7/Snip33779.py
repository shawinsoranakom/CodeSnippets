def test_ifchanged03(self):
        output = self.engine.render_to_string("ifchanged03", {"num": (1, 1, 1)})
        self.assertEqual(output, "1")