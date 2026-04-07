def test_secure_param_non_https_urls(self):
        insecure_urls = (
            "http://example.com/p",
            "ftp://example.com/p",
            "//example.com/p",
        )
        for url in insecure_urls:
            with self.subTest(url=url):
                self.assertIs(
                    url_has_allowed_host_and_scheme(
                        url, allowed_hosts={"example.com"}, require_https=True
                    ),
                    False,
                )