def test_urlfield_assume_scheme_when_colons(self):
        f = URLField()
        tests = [
            # Port number.
            ("http://example.com:8080/", "http://example.com:8080/"),
            ("https://example.com:443/path", "https://example.com:443/path"),
            # Userinfo with password.
            ("http://user:pass@example.com", "http://user:pass@example.com"),
            (
                "http://user:pass@example.com:8080/",
                "http://user:pass@example.com:8080/",
            ),
            # Colon in path segment.
            ("http://example.com/path:segment", "http://example.com/path:segment"),
            ("http://example.com/a:b/c:d", "http://example.com/a:b/c:d"),
            # Colon in query string.
            ("http://example.com/?key=val:ue", "http://example.com/?key=val:ue"),
            # Colon in fragment.
            ("http://example.com/#section:1", "http://example.com/#section:1"),
            # IPv6 -- multiple colons in host.
            ("http://[::1]/", "http://[::1]/"),
            ("http://[2001:db8::1]/", "http://[2001:db8::1]/"),
            ("http://[2001:db8::1]:8080/", "http://[2001:db8::1]:8080/"),
            # Colons across multiple components.
            (
                "http://user:pass@example.com:8080/path:x?q=a:b#id:1",
                "http://user:pass@example.com:8080/path:x?q=a:b#id:1",
            ),
            # FTP with port and userinfo.
            (
                "ftp://user:pass@ftp.example.com:21/file",
                "ftp://user:pass@ftp.example.com:21/file",
            ),
            (
                "ftps://user:pass@ftp.example.com:990/",
                "ftps://user:pass@ftp.example.com:990/",
            ),
            # Scheme-relative URLs, starts with "//".
            ("//example.com:8080/path", "https://example.com:8080/path"),
            ("//user:pass@example.com/", "https://user:pass@example.com/"),
        ]
        for value, expected in tests:
            with self.subTest(value=value):
                self.assertEqual(f.clean(value), expected)