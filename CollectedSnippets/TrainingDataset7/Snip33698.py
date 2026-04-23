def test_if_tag_not_in_02(self):
        output = self.engine.render_to_string("if-tag-not-in-02", {"x": [1]})
        self.assertEqual(output, "yes")