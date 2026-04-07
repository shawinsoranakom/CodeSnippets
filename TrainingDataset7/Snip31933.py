def test_default_expiry(self):
        self.assertEqual(self.session.get_expiry_age(), self.custom_session_cookie_age)
        self.session.set_expiry(0)
        self.assertEqual(self.session.get_expiry_age(), self.custom_session_cookie_age)