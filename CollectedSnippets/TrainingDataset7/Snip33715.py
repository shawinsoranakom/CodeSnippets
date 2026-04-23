def test_if_tag_or09(self):
        """
        multiple ORs
        """
        output = self.engine.render_to_string("if-tag-or09", {"baz": True})
        self.assertEqual(output, "yes")