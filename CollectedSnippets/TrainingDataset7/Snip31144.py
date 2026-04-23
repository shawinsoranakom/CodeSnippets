def test_url_path(self):
        """
        Passing a URL path to resolve_url() results in the same url.
        """
        self.assertEqual("/something/", resolve_url("/something/"))