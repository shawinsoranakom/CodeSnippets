def test_domain(self):
        """
        Passing a domain to resolve_url() returns the same domain.
        """
        self.assertEqual(resolve_url("example.com"), "example.com")