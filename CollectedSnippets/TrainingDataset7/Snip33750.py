def test_if_tag_error03(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("if-tag-error03", {"foo": True})