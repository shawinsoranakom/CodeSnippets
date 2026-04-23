def test_email_tls_default_disabled(self):
        backend = smtp.EmailBackend()
        self.assertFalse(backend.use_tls)