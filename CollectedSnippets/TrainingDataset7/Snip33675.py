def test_if_tag_filter01(self):
        output = self.engine.render_to_string("if-tag-filter01", {"foo": "abcde"})
        self.assertEqual(output, "yes")