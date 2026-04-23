def test_login_redirect_url_overrides_next_page(self):
        response = self.login(url="/login/next_page/?next=/test/")
        self.assertRedirects(response, "/test/", fetch_redirect_response=False)