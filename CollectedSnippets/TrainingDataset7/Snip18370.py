def test_standard_login_url(self):
        self.assertLoginURLEquals("/login/?next=/login_required/")