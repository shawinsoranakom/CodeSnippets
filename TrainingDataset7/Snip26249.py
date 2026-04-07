def test_email_ssl_certfile_default_disabled(self):
        backend = smtp.EmailBackend()
        self.assertIsNone(backend.ssl_certfile)