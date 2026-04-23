def test_basic(self):
        environ = {
            "CONTENT_TYPE": "text/html",
            "CONTENT_LENGTH": "100",
            "HTTP_HOST": "example.com",
        }
        headers = HttpHeaders(environ)
        self.assertEqual(sorted(headers), ["Content-Length", "Content-Type", "Host"])
        self.assertEqual(
            headers,
            {
                "Content-Type": "text/html",
                "Content-Length": "100",
                "Host": "example.com",
            },
        )