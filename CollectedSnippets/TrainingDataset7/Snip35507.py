def test_get_current_timezone_templatetag_invalid_argument(self):
        msg = (
            "'get_current_timezone' requires 'as variable' (got "
            "['get_current_timezone'])"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Template("{% load tz %}{% get_current_timezone %}").render()