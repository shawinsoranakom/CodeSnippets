def test_get_current_site_host_with_trailing_dot(self):
        """
        The site is matched if the name in the request has a trailing dot.
        """
        request = HttpRequest()
        request.META = {
            "SERVER_NAME": "example.com.",
            "SERVER_PORT": "80",
        }
        site = get_current_site(request)
        self.assertEqual(site.name, "example.com")