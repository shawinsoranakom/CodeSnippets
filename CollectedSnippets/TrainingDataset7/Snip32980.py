def test_length03(self):
        output = self.engine.render_to_string("length03", {"string": ""})
        self.assertEqual(output, "0")