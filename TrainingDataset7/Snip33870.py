def test_multiline01(self):
        output = self.engine.render_to_string("multiline01")
        self.assertEqual(output, multiline_string)