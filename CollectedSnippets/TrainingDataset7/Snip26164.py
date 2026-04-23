def test_send_mail_auth_conflict(self):
        msg = (
            "auth_user and auth_password cannot be used with a connection. "
            "Pass auth_user and auth_password to get_connection() instead."
        )
        for param in ["auth_user", "auth_password"]:
            with (
                self.subTest(param=param),
                self.assertRaisesMessage(TypeError, msg),
            ):
                mail.send_mail(
                    "subject",
                    "body",
                    "from@example.com",
                    ["to@example.com"],
                    **{param: "value"},
                    connection=mail.get_connection(),
                )