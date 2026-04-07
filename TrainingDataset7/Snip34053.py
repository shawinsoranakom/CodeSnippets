def test_widthratio02(self):
        output = self.engine.render_to_string("widthratio02", {"a": 0, "b": 0})
        self.assertEqual(output, "0")