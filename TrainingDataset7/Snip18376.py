def test_lazy_login_url(self):
        self.assertLoginURLEquals("/login/?next=/login_required/")