def test_redirect_https(self):
        """GET a URL that redirects to an HTTPS URI."""
        response = self.client.get("/https_redirect_view/", follow=True)
        self.assertTrue(response.test_was_secure_request)