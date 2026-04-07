def test_syntax_error_duplicate_option(self):
        msg = "The 'noop' option was specified more than once."
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")