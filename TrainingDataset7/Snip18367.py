def test_login_redirect_url_overrides_get_default_redirect_url(self):
        response = self.login(url="/login/get_default_redirect_url/?next=/test/")
        self.assertRedirects(response, "/test/", fetch_redirect_response=False)