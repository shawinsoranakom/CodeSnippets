def test_create_user_email_domain_normalize_rfc3696(self):
        # According to RFC 3696 Section 3 the "@" symbol can be part of the
        # local part of an email address.
        returned = UserManager.normalize_email(r"Abc\@DEF@EXAMPLE.com")
        self.assertEqual(returned, r"Abc\@DEF@example.com")