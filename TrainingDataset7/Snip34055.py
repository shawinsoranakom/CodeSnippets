def test_widthratio04(self):
        output = self.engine.render_to_string("widthratio04", {"a": 50, "b": 100})
        self.assertEqual(output, "50")