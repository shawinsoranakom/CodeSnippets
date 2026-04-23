def test_if_tag_noteq04(self):
        output = self.engine.render_to_string("if-tag-noteq04", {"foo": 1, "bar": 2})
        self.assertEqual(output, "yes")