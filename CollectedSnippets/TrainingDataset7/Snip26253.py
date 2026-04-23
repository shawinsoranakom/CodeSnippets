def test_email_tls_attempts_starttls(self):
        backend = smtp.EmailBackend()
        self.assertTrue(backend.use_tls)
        with self.assertRaisesMessage(
            SMTPException, "STARTTLS extension not supported by server."
        ):
            with backend:
                pass