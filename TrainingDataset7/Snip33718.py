def test_if_tag_not06(self):
        output = self.engine.render_to_string("if-tag-not06")
        self.assertEqual(output, "no")