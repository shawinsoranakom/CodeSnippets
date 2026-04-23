def test_valid_urls(self):
        self.assertEqual(check_csrf_trusted_origins(None), [])