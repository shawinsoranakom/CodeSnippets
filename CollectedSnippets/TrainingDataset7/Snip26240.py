def test_email_tls_use_settings(self):
        backend = smtp.EmailBackend()
        self.assertTrue(backend.use_tls)