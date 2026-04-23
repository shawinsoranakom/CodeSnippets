def test_login_next_page_overrides_login_redirect_url_setting(self):
        response = self.login(url="/login/next_page/")
        self.assertRedirects(response, "/somewhere/", fetch_redirect_response=False)