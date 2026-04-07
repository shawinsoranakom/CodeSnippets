def test_default(self):
        """Stay on the login page by default."""
        self.login()
        response = self.client.get(self.dont_redirect_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["next"], "")