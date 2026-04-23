def test_if_tag_filter02(self):
        output = self.engine.render_to_string("if-tag-filter02")
        self.assertEqual(output, "no")