def test_with_csrf_cookie_secure_true(self):
        self.assertEqual(csrf.check_csrf_cookie_secure(None), [])