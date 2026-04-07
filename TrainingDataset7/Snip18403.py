def test_logout_doesnt_cache(self):
        """
        The logout() view should send "no-cache" headers for reasons described
        in #25490.
        """
        response = self.client.post("/logout/")
        self.assertIn("no-store", response.headers["Cache-Control"])