def test_login_get_default_redirect_url(self):
        response = self.login(url="/login/get_default_redirect_url/")
        self.assertRedirects(response, "/custom/", fetch_redirect_response=False)