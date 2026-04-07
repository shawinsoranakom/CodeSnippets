def test_allowed_hosts_str(self):
        self.assertIs(
            url_has_allowed_host_and_scheme(
                "http://good.com/good", allowed_hosts="good.com"
            ),
            True,
        )
        self.assertIs(
            url_has_allowed_host_and_scheme(
                "http://good.co/evil", allowed_hosts="good.com"
            ),
            False,
        )