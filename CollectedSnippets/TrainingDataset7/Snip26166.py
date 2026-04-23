def test_send_mass_mail_fail_silently_conflict(self):
        datatuple = (("Subject", "Message", "from@example.com", ["to@example.com"]),)
        msg = (
            "fail_silently cannot be used with a connection. "
            "Pass fail_silently to get_connection() instead."
        )
        with self.assertRaisesMessage(TypeError, msg):
            mail.send_mass_mail(
                datatuple, fail_silently=True, connection=mail.get_connection()
            )