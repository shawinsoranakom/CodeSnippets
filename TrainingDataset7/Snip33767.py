def test_if_tag_single_eq(self):
        # A single equals sign is a syntax error.
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("if-tag-single-eq", {"foo": 1})