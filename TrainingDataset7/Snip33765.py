def test_if_tag_badarg03(self):
        output = self.engine.render_to_string("if-tag-badarg03", {"y": 1})
        self.assertEqual(output, "yes")