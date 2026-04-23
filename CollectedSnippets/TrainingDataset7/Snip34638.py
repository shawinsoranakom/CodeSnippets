def test_external_redirect_without_trailing_slash(self):
        """
        Client._handle_redirects() with an empty path.
        """
        response = self.client.get("/no_trailing_slash_external_redirect/", follow=True)
        self.assertRedirects(response, "https://testserver")