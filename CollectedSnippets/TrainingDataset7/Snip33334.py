def test_no_as_var(self):
        msg = (
            "'get_current_language_bidi' requires 'as variable' (got "
            "['get_current_language_bidi'])"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")