def test_page_not_found(self):
        "A 404 status is returned by the page_not_found view"
        for url in self.nonexistent_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
        self.assertIn(b"<h1>Not Found</h1>", response.content)
        self.assertIn(
            b"<p>The requested resource was not found on this server.</p>",
            response.content,
        )