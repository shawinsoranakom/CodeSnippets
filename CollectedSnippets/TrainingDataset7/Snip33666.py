def test_if_tag05(self):
        output = self.engine.render_to_string("if-tag05", {"bar": True})
        self.assertEqual(output, "bar")