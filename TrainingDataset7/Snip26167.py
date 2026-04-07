def test_send_mass_mail_auth_conflict(self):
        datatuple = (("Subject", "Message", "from@example.com", ["to@example.com"]),)
        msg = (
            "auth_user and auth_password cannot be used with a connection. "
            "Pass auth_user and auth_password to get_connection() instead."
        )
        for param in ["auth_user", "auth_password"]:
            with (
                self.subTest(param=param),
                self.assertRaisesMessage(TypeError, msg),
            ):
                mail.send_mass_mail(
                    datatuple, **{param: "value"}, connection=mail.get_connection()
                )