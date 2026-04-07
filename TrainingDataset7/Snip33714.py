def test_if_tag_or08(self):
        output = self.engine.render_to_string("if-tag-or08", {"bar": True})
        self.assertEqual(output, "yes")