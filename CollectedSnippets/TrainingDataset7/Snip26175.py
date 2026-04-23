def test_mail_managers(self):
        with self.assertDeprecatedIn70(
            "'fail_silently', 'connection', 'html_message'", "mail_managers"
        ):
            mail_managers(
                "subject",
                "message",
                # Deprecated positional args:
                None,
                mail.get_connection(),
                "html message",
            )