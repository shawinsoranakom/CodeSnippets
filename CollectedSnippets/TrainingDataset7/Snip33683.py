def test_if_tag_noteq02(self):
        output = self.engine.render_to_string("if-tag-noteq02", {"foo": 1})
        self.assertEqual(output, "yes")