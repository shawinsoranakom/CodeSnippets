def test_email_ssl_certfile_override_settings(self):
        backend = smtp.EmailBackend(ssl_certfile="bar")
        self.assertEqual(backend.ssl_certfile, "bar")