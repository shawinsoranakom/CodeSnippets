def test_basic_auth(self):
        # Valid basic auth credentials are allowed.
        self.assertIs(
            url_has_allowed_host_and_scheme(
                r"http://user:pass@testserver/", allowed_hosts={"user:pass@testserver"}
            ),
            True,
        )