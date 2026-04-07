def test_if_tag_error05(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("if-tag-error05", {"foo": True})