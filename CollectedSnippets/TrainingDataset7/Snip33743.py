def test_if_tag_not31(self):
        output = self.engine.render_to_string("if-tag-not31")
        self.assertEqual(output, "yes")