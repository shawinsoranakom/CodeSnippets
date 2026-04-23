def test_send_mass_mail(self):
        with self.assertDeprecatedIn70(
            "'fail_silently', 'auth_user', 'auth_password', 'connection'",
            "send_mass_mail",
        ):
            send_mass_mail(
                [],
                # Deprecated positional args:
                None,
                None,
                None,
                mail.get_connection(),
            )