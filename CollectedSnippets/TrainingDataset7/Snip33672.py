def test_if_tag11(self):
        output = self.engine.render_to_string("if-tag11", {"bar": True})
        self.assertEqual(output, "bar")