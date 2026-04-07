def test_with_ssl_redirect(self):
        self.assertEqual(base.check_ssl_redirect(None), [])