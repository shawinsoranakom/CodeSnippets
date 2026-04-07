def test_inheritance32(self):
        output = self.engine.render_to_string("inheritance32")
        self.assertEqual(output, "13")