def test_if_tag08(self):
        output = self.engine.render_to_string("if-tag08", {"bar": True})
        self.assertEqual(output, "bar")