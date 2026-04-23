def test_mail_admins(self):
        with self.assertDeprecatedIn70(
            "'fail_silently', 'connection', 'html_message'", "mail_admins"
        ):
            mail_admins(
                "subject",
                "message",
                # Deprecated positional args:
                None,
                mail.get_connection(),
                "html message",
            )