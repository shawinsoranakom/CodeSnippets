def test_bad(self):
        for pair in (
            ("example2.com", "example.com"),
            ("foo.example.com", "example.com"),
            ("example.com:9999", "example.com:8888"),
            ("foo.example.com:8888", ""),
        ):
            self.assertIs(is_same_domain(*pair), False)