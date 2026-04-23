def test_good_urls(self):
        good_urls = (
            "/view/?param=http://example.com",
            "/view/?param=https://example.com",
            "/view?param=ftp://example.com",
            "view/?param=//example.com",
            "https://testserver/",
            "HTTPS://testserver/",
            "//testserver/",
            "http://testserver/confirm?email=me@example.com",
            "/url%20with%20spaces/",
            "path/http:2222222222",
        )
        for good_url in good_urls:
            with self.subTest(url=good_url):
                self.assertIs(
                    url_has_allowed_host_and_scheme(
                        good_url, allowed_hosts={"otherserver", "testserver"}
                    ),
                    True,
                )