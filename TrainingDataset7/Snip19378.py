def test_with_csrf_cookie_secure_truthy(self):
        """CSRF_COOKIE_SECURE must be boolean."""
        self.assertEqual(csrf.check_csrf_cookie_secure(None), [csrf.W016])