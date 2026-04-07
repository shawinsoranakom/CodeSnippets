def test_if_tag_not26(self):
        output = self.engine.render_to_string("if-tag-not26")
        self.assertEqual(output, "yes")