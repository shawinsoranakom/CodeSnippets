def test_csrf_token_in_404(self):
        """
        The 404 page should have the csrf_token available in the context
        """
        # See ticket #14565
        for url in self.nonexistent_urls:
            response = self.client.get(url)
            self.assertNotEqual(response.content, b"NOTPROVIDED")
            self.assertNotEqual(response.content, b"")