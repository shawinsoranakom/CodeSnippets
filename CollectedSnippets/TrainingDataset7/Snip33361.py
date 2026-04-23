def test_syntax_error_context_as(self, tag_name):
        msg = (
            f"Invalid argument 'as' provided to the '{tag_name}' tag for the context "
            f"option"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")