def test_if_tag_eq03(self):
        output = self.engine.render_to_string("if-tag-eq03", {"foo": 1, "bar": 1})
        self.assertEqual(output, "yes")