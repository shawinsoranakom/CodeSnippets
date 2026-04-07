def test_send_mail_fail_silently_conflict(self):
        msg = (
            "fail_silently cannot be used with a connection. "
            "Pass fail_silently to get_connection() instead."
        )
        with self.assertRaisesMessage(TypeError, msg):
            mail.send_mail(
                "Subject",
                "Body",
                "from@example.com",
                ["to@example.com"],
                fail_silently=True,
                connection=mail.get_connection(),
            )