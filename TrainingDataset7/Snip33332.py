def test_no_as_var(self):
        msg = (
            "'get_available_languages' requires 'as variable' (got "
            "['get_available_languages', 'a', 'langs'])"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("syntax_i18n")