def test_login_url_with_querystring(self):
        self.assertLoginURLEquals("/login/?pretty=1&next=/login_required/")