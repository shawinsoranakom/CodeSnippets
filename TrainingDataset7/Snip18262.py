def test_password_validators_help_text_html_escaping(self):
        class AmpersandValidator:
            def get_help_text(self):
                return "Must contain &"

        help_text = password_validators_help_text_html([AmpersandValidator()])
        self.assertEqual(help_text, "<ul><li>Must contain &amp;</li></ul>")
        # help_text is marked safe and therefore unchanged by
        # conditional_escape().
        self.assertEqual(help_text, conditional_escape(help_text))