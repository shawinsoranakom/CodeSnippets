def test_mail_managers_fail_silently_conflict(self):
        msg = (
            "fail_silently cannot be used with a connection. "
            "Pass fail_silently to get_connection() instead."
        )
        with self.assertRaisesMessage(TypeError, msg):
            mail.mail_managers(
                "Subject",
                "Message",
                fail_silently=True,
                connection=mail.get_connection(),
            )