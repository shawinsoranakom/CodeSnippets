def test_basic_syntax27(self):
        output = self.engine.render_to_string("basic-syntax27")
        self.assertEqual(output, '"fred"')