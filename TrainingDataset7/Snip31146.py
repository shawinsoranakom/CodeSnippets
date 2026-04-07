def test_full_url(self):
        """
        Passing a full URL to resolve_url() results in the same url.
        """
        url = "http://example.com/"
        self.assertEqual(url, resolve_url(url))