def test_widthratio03(self):
        output = self.engine.render_to_string("widthratio03", {"a": 0, "b": 100})
        self.assertEqual(output, "0")