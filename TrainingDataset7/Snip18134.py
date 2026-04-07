def test_create_user_email_domain_normalize_with_whitespace(self):
        returned = UserManager.normalize_email(r"email\ with_whitespace@D.COM")
        self.assertEqual(returned, r"email\ with_whitespace@d.com")