def test_redirect_shortcircuits_non_404_response(self):
        """RedirectFallbackMiddleware short-circuits on non-404 requests."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)