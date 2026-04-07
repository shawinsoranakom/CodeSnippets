def test_named_login_url(self):
        self.assertLoginURLEquals("/login/?next=/login_required/")