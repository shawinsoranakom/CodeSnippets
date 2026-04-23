def test_email_ssl_use_settings(self):
        backend = smtp.EmailBackend()
        self.assertTrue(backend.use_ssl)