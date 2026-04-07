def test_login_named_next_page_named(self):
        response = self.login(url="/login/next_page/named/")
        self.assertRedirects(
            response, "/password_reset/", fetch_redirect_response=False
        )