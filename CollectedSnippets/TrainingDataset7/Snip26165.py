def test_email_message_send_fail_silently_conflict(self):
        email = mail.EmailMessage(
            "Subject",
            "Body",
            "from@example.com",
            ["to@example.com"],
            connection=mail.get_connection(),
        )
        msg = (
            "fail_silently cannot be used with a connection. "
            "Pass fail_silently to get_connection() instead."
        )
        with self.assertRaisesMessage(TypeError, msg):
            email.send(fail_silently=True)