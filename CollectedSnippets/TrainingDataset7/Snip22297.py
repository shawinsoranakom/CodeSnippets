def test_post_fallback_flatpage(self):
        """
        POSTing to a flatpage served by the middleware will raise a CSRF error
        if no token is provided.
        """
        response = self.client.post("/flatpage/")
        self.assertEqual(response.status_code, 403)