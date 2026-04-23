def test_logout_with_overridden_redirect_url(self):
        # Bug 11223
        self.login()
        response = self.client.post("/logout/next_page/")
        self.assertRedirects(response, "/somewhere/", fetch_redirect_response=False)

        response = self.client.post("/logout/next_page/?next=/login/")
        self.assertRedirects(response, "/login/", fetch_redirect_response=False)

        self.confirm_logged_out()