def test_max_url_length(self):
        allowed_host = "example.com"
        max_extra_characters = "é" * (MAX_URL_LENGTH - len(allowed_host) - 1)
        max_length_boundary_url = f"{allowed_host}/{max_extra_characters}"
        cases = [
            (max_length_boundary_url, True),
            (max_length_boundary_url + "ú", False),
        ]
        for url, expected in cases:
            with self.subTest(url=url):
                self.assertIs(
                    url_has_allowed_host_and_scheme(url, allowed_hosts={allowed_host}),
                    expected,
                )