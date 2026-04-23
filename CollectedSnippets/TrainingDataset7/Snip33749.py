def test_if_tag_error02(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("if-tag-error02", {"foo": True})