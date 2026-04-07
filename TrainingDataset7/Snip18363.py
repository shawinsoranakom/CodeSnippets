def test_login_next_page(self):
        response = self.login(url="/login/next_page/")
        self.assertRedirects(response, "/somewhere/", fetch_redirect_response=False)