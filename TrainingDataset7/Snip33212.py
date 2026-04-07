def test_https(self):
        self.assertEqual(
            urlize("https://google.com"),
            '<a href="https://google.com" rel="nofollow">https://google.com</a>',
        )