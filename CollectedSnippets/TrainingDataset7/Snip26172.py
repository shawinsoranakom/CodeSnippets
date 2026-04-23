def test_send_mail(self):
        with self.assertDeprecatedIn70(
            "'fail_silently', 'auth_user', 'auth_password', 'connection', "
            "'html_message'",
            "send_mail",
        ):
            send_mail(
                "subject",
                "message",
                "from@example.com",
                ["to@example.com"],
                # Deprecated positional args:
                None,
                None,
                None,
                mail.get_connection(),
                "html message",
            )