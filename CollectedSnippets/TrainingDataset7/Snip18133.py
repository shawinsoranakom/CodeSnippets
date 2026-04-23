def test_create_user_email_domain_normalize(self):
        returned = UserManager.normalize_email("normal@DOMAIN.COM")
        self.assertEqual(returned, "normal@domain.com")