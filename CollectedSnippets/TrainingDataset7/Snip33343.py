def test_no_arg(self):
        with self.assertRaisesMessage(
            TemplateSyntaxError, "'language' takes one argument (language)"
        ):
            self.engine.render_to_string("i18n_language")