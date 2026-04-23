def test_smart_urlquote(self):
        items = (
            # IDN is encoded as percent-encoded ("quoted") UTF-8 (#36013).
            ("http://öäü.com/", "http://%C3%B6%C3%A4%C3%BC.com/"),
            ("https://faß.example.com", "https://fa%C3%9F.example.com"),
            (
                "http://öäü.com/öäü/",
                "http://%C3%B6%C3%A4%C3%BC.com/%C3%B6%C3%A4%C3%BC/",
            ),
            (
                # Valid under IDNA 2008, but was invalid in IDNA 2003.
                "https://މިހާރު.com",
                "https://%DE%89%DE%A8%DE%80%DE%A7%DE%83%DE%AA.com",
            ),
            (
                # Valid under WHATWG URL Specification but not IDNA 2008.
                "http://👓.ws",
                "http://%F0%9F%91%93.ws",
            ),
            # Pre-encoded IDNA is left unchanged.
            ("http://xn--iny-zx5a.com/idna2003", "http://xn--iny-zx5a.com/idna2003"),
            ("http://xn--fa-hia.com/idna2008", "http://xn--fa-hia.com/idna2008"),
            # Everything unsafe is quoted, !*'();:@&=+$,/?#[]~ is considered
            # safe as per RFC.
            (
                "http://example.com/path/öäü/",
                "http://example.com/path/%C3%B6%C3%A4%C3%BC/",
            ),
            ("http://example.com/%C3%B6/ä/", "http://example.com/%C3%B6/%C3%A4/"),
            ("http://example.com/?x=1&y=2+3&z=", "http://example.com/?x=1&y=2+3&z="),
            ("http://example.com/?x=<>\"'", "http://example.com/?x=%3C%3E%22%27"),
            (
                "http://example.com/?q=http://example.com/?x=1%26q=django",
                "http://example.com/?q=http%3A%2F%2Fexample.com%2F%3Fx%3D1%26q%3D"
                "django",
            ),
            (
                "http://example.com/?q=http%3A%2F%2Fexample.com%2F%3Fx%3D1%26q%3D"
                "django",
                "http://example.com/?q=http%3A%2F%2Fexample.com%2F%3Fx%3D1%26q%3D"
                "django",
            ),
            ("http://.www.f oo.bar/", "http://.www.f%20oo.bar/"),
            ('http://example.com">', "http://example.com%22%3E"),
            ("http://10.22.1.1/", "http://10.22.1.1/"),
            ("http://[fd00::1]/", "http://[fd00::1]/"),
        )
        for value, output in items:
            with self.subTest(value=value, output=output):
                self.assertEqual(smart_urlquote(value), output)