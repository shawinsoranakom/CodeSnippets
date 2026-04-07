def test_widthratio10(self):
        output = self.engine.render_to_string("widthratio10", {"a": 50, "b": 100})
        self.assertEqual(output, "50")