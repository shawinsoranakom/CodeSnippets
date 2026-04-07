def test_secure_param_https_urls(self):
        secure_urls = (
            "https://example.com/p",
            "HTTPS://example.com/p",
            "/view/?param=http://example.com",
        )
        for url in secure_urls:
            with self.subTest(url=url):
                self.assertIs(
                    url_has_allowed_host_and_scheme(
                        url, allowed_hosts={"example.com"}, require_https=True
                    ),
                    True,
                )