def test_redirect_url(self):
        """If logged in, go to custom redirected URL."""
        self.login()
        response = self.client.get(self.do_redirect_url)
        self.assertRedirects(response, "/custom/", fetch_redirect_response=False)