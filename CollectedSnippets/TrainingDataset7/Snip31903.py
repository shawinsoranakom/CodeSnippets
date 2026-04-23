def test_default_expiry(self):
        # A normal session has a max age equal to settings
        self.assertEqual(self.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

        # So does a custom session with an idle expiration time of 0 (but it'll
        # expire at browser close)
        self.session.set_expiry(0)
        self.assertEqual(self.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)