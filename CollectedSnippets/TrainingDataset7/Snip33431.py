def test_basic_syntax26(self):
        output = self.engine.render_to_string("basic-syntax26")
        self.assertEqual(output, '"fred"')