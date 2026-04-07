def test_redirect_http(self):
        """GET a URL that redirects to an HTTP URI."""
        response = self.client.get("/http_redirect_view/", follow=True)
        self.assertFalse(response.test_was_secure_request)