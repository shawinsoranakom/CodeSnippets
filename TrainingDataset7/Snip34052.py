def test_widthratio01(self):
        output = self.engine.render_to_string("widthratio01", {"a": 50, "b": 100})
        self.assertEqual(output, "0")