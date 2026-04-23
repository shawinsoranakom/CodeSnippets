def test_split_domain_port(self):
        for host, expected in [
            ("<invalid>", ("", "")),
            ("<invalid>:8080", ("", "")),
            ("example.com 8080", ("", "")),
            ("example.com:invalid", ("", "")),
            ("[::1]", ("[::1]", "")),
            ("[::1]:8080", ("[::1]", "8080")),
            ("[::ffff:127.0.0.1]", ("[::ffff:127.0.0.1]", "")),
            ("[::ffff:127.0.0.1]:8080", ("[::ffff:127.0.0.1]", "8080")),
            (
                "[1851:0000:3238:DEF1:0177:0000:0000:0125]",
                ("[1851:0000:3238:def1:0177:0000:0000:0125]", ""),
            ),
            (
                "[1851:0000:3238:DEF1:0177:0000:0000:0125]:8080",
                ("[1851:0000:3238:def1:0177:0000:0000:0125]", "8080"),
            ),
            ("127.0.0.1", ("127.0.0.1", "")),
            ("127.0.0.1:8080", ("127.0.0.1", "8080")),
            ("example.com", ("example.com", "")),
            ("example.com:8080", ("example.com", "8080")),
            ("example.com.", ("example.com", "")),
            ("example.com.:8080", ("example.com", "8080")),
            ("xn--n28h.test", ("xn--n28h.test", "")),
            ("xn--n28h.test:8080", ("xn--n28h.test", "8080")),
            ("subdomain.example.com", ("subdomain.example.com", "")),
            ("subdomain.example.com:8080", ("subdomain.example.com", "8080")),
        ]:
            with self.subTest(host=host):
                self.assertEqual(split_domain_port(host), expected)