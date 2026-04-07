def test_if_tag_noteq03(self):
        output = self.engine.render_to_string("if-tag-noteq03", {"foo": 1, "bar": 1})
        self.assertEqual(output, "no")