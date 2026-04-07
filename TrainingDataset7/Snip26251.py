def test_email_ssl_keyfile_override_settings(self):
        backend = smtp.EmailBackend(ssl_keyfile="bar")
        self.assertEqual(backend.ssl_keyfile, "bar")