def test_no_allowed_hosts(self):
        # A path without host is allowed.
        self.assertIs(
            url_has_allowed_host_and_scheme(
                "/confirm/me@example.com", allowed_hosts=None
            ),
            True,
        )
        # Basic auth without host is not allowed.
        self.assertIs(
            url_has_allowed_host_and_scheme(
                r"http://testserver\@example.com", allowed_hosts=None
            ),
            False,
        )