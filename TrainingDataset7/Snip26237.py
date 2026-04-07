def test_auth_attempted(self):
        """
        Opening the backend with non empty username/password tries
        to authenticate against the SMTP server.
        """
        backend = smtp.EmailBackend(
            username="not empty username", password="not empty password"
        )
        with self.assertRaisesMessage(
            SMTPException, "SMTP AUTH extension not supported by server."
        ):
            with backend:
                pass