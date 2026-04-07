def test_email_tls_override_settings(self):
        backend = smtp.EmailBackend(use_tls=False)
        self.assertFalse(backend.use_tls)