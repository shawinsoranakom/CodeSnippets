def test_ipv4(self):
        self.assertEqual(
            urlize("http://192.168.0.15/api/9"),
            '<a href="http://192.168.0.15/api/9" rel="nofollow">'
            "http://192.168.0.15/api/9</a>",
        )