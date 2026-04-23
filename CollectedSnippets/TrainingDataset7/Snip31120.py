def test_host_validation_in_debug_mode(self):
        """
        If ALLOWED_HOSTS is empty and DEBUG is True, variants of localhost are
        allowed.
        """
        valid_hosts = ["localhost", "subdomain.localhost", "127.0.0.1", "[::1]"]
        for host in valid_hosts:
            request = HttpRequest()
            request.META = {"HTTP_HOST": host}
            self.assertEqual(request.get_host(), host)

        # Other hostnames raise a DisallowedHost.
        with self.assertRaises(DisallowedHost):
            request = HttpRequest()
            request.META = {"HTTP_HOST": "example.com"}
            request.get_host()