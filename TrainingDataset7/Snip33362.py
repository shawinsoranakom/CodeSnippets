def test_syntax_error_context_noop(self, tag_name):
        msg = (
            f"Invalid argument 'noop' provided to the '{tag_name}' tag for the context "
            f"option"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")