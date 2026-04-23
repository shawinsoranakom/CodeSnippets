def test_widthratio16(self):
        output = self.engine.render_to_string("widthratio16", {"a": 50, "b": 100})
        self.assertEqual(output, "-50-")