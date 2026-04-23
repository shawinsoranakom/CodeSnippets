def test_email_timeout_override_settings(self):
        backend = smtp.EmailBackend()
        self.assertEqual(backend.timeout, 10)