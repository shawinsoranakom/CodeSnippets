def test_relative_redirect(self):
        response = self.client.get("/accounts/")
        self.assertRedirects(response, "/accounts/login/")