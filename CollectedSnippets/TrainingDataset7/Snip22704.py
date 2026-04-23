def test_urlfield_clean(self):
        f = URLField(required=False)
        tests = [
            ("http://localhost", "http://localhost"),
            ("http://example.com", "http://example.com"),
            ("http://example.com/test", "http://example.com/test"),
            ("http://example.com.", "http://example.com."),
            ("http://www.example.com", "http://www.example.com"),
            ("http://www.example.com:8000/test", "http://www.example.com:8000/test"),
            (
                "http://example.com?some_param=some_value",
                "http://example.com?some_param=some_value",
            ),
            ("valid-with-hyphens.com", "https://valid-with-hyphens.com"),
            ("subdomain.domain.com", "https://subdomain.domain.com"),
            ("http://200.8.9.10", "http://200.8.9.10"),
            ("http://200.8.9.10:8000/test", "http://200.8.9.10:8000/test"),
            ("http://valid-----hyphens.com", "http://valid-----hyphens.com"),
            (
                "http://some.idn.xyzäöüßabc.domain.com:123/blah",
                "http://some.idn.xyz\xe4\xf6\xfc\xdfabc.domain.com:123/blah",
            ),
            (
                "www.example.com/s/http://code.djangoproject.com/ticket/13804",
                "https://www.example.com/s/http://code.djangoproject.com/ticket/13804",
            ),
            # Normalization.
            ("http://example.com/     ", "http://example.com/"),
            # Valid IDN.
            ("http://עברית.idn.icann.org/", "http://עברית.idn.icann.org/"),
            ("http://sãopaulo.com/", "http://sãopaulo.com/"),
            ("http://sãopaulo.com.br/", "http://sãopaulo.com.br/"),
            ("http://пример.испытание/", "http://пример.испытание/"),
            ("http://مثال.إختبار/", "http://مثال.إختبار/"),
            ("http://例子.测试/", "http://例子.测试/"),
            ("http://例子.測試/", "http://例子.測試/"),
            (
                "http://उदाहरण.परीक्षा/",
                "http://उदाहरण.परीक्षा/",
            ),
            ("http://例え.テスト/", "http://例え.テスト/"),
            ("http://مثال.آزمایشی/", "http://مثال.آزمایشی/"),
            ("http://실례.테스트/", "http://실례.테스트/"),
            ("http://العربية.idn.icann.org/", "http://العربية.idn.icann.org/"),
            # IPv6.
            ("http://[12:34::3a53]/", "http://[12:34::3a53]/"),
            ("http://[a34:9238::]:8080/", "http://[a34:9238::]:8080/"),
            # IPv6 without scheme.
            ("[12:34::3a53]/", "https://[12:34::3a53]/"),
            # IDN domain without scheme but with port.
            ("ñandú.es:8080/", "https://ñandú.es:8080/"),
            # Scheme-relative.
            ("//example.com", "https://example.com"),
            ("//example.com/path", "https://example.com/path"),
            # Whitespace stripped.
            ("\t\n//example.com  \n\t\n", "https://example.com"),
            ("\t\nhttp://example.com  \n\t\n", "http://example.com"),
        ]
        for url, expected in tests:
            with self.subTest(url=url):
                self.assertEqual(f.clean(url), expected)