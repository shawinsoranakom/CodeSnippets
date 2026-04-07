def test_redirect(self):
        """If logged in, go to default redirected URL."""
        self.login()
        response = self.client.get(self.do_redirect_url)
        self.assertRedirects(
            response, "/accounts/profile/", fetch_redirect_response=False
        )