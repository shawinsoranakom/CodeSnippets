def test_get_login_url_from_settings(self):
        login_url = self.middleware.get_login_url(lambda: None)
        self.assertEqual(login_url, "/settings_login/")