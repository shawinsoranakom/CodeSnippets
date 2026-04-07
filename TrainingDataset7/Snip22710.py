def test_urlfield_assume_scheme(self):
        f = URLField()
        self.assertEqual(f.clean("example.com"), "https://example.com")
        f = URLField(assume_scheme="http")
        self.assertEqual(f.clean("example.com"), "http://example.com")
        f = URLField(assume_scheme="https")
        self.assertEqual(f.clean("example.com"), "https://example.com")