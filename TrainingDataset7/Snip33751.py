def test_if_tag_error04(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("if-tag-error04", {"foo": True})