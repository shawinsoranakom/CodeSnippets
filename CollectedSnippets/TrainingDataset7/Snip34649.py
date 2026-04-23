def test_relative_redirect_no_trailing_slash(self):
        response = self.client.get("/accounts/no_trailing_slash")
        self.assertRedirects(response, "/accounts/login/")