def test_no_redirect_on_404(self):
        """
        A request for a nonexistent URL shouldn't cause a redirect to
        /<default_language>/<request_url> when prefix_default_language=False
        and /<default_language>/<request_url> has a URL match (#27402).
        """
        # A match for /group1/group2/ must exist for this to act as a
        # regression test.
        response = self.client.get("/group1/group2/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/nonexistent/")
        self.assertEqual(response.status_code, 404)