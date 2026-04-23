def test_widthratio05(self):
        output = self.engine.render_to_string("widthratio05", {"a": 100, "b": 100})
        self.assertEqual(output, "100")