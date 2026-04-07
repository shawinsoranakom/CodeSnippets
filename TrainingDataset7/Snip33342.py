def test_no_for_as(self):
        msg = (
            "'get_language_info_list' requires 'for sequence as variable' (got "
            "['error'])"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("i18n_syntax")