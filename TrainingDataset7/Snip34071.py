def test_widthratio17(self):
        output = self.engine.render_to_string("widthratio17", {"a": 100, "b": 100})
        self.assertEqual(output, "-100-")