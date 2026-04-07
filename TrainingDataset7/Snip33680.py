def test_if_tag_eq04(self):
        output = self.engine.render_to_string("if-tag-eq04", {"foo": 1, "bar": 2})
        self.assertEqual(output, "no")