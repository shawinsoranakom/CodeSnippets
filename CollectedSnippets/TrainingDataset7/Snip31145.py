def test_relative_path(self):
        """
        Passing a relative URL path to resolve_url() results in the same url.
        """
        self.assertEqual("../", resolve_url("../"))
        self.assertEqual("../relative/", resolve_url("../relative/"))
        self.assertEqual("./", resolve_url("./"))
        self.assertEqual("./relative/", resolve_url("./relative/"))