def test_if_tag_not21(self):
        output = self.engine.render_to_string("if-tag-not21")
        self.assertEqual(output, "yes")