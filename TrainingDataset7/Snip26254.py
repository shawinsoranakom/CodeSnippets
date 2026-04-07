def test_email_ssl_attempts_ssl_connection(self):
        backend = smtp.EmailBackend()
        self.assertTrue(backend.use_ssl)
        with self.assertRaises(SSLError):
            with backend:
                pass