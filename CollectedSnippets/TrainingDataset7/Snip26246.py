def test_email_ssl_default_disabled(self):
        backend = smtp.EmailBackend()
        self.assertFalse(backend.use_ssl)