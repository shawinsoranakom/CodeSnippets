def test_email_ssl_keyfile_default_disabled(self):
        backend = smtp.EmailBackend()
        self.assertIsNone(backend.ssl_keyfile)