def test_syntax_error_missing_context(self, tag_name):
        msg = "No argument provided to the '{}' tag for the context option.".format(
            tag_name
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")