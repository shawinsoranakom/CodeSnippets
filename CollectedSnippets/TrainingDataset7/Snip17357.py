def test_multiple_cookie_headers_http2(self):
        test_cases = [
            {
                "label": "RFC-compliant headers (no semicolon)",
                "headers": [
                    (b"cookie", b"a=abc"),
                    (b"cookie", b"b=def"),
                    (b"cookie", b"c=ghi"),
                ],
            },
            {
                # Some clients may send cookies with trailing semicolons.
                "label": "Headers with trailing semicolons",
                "headers": [
                    (b"cookie", b"a=abc;"),
                    (b"cookie", b"b=def;"),
                    (b"cookie", b"c=ghi;"),
                ],
            },
        ]

        for case in test_cases:
            with self.subTest(case["label"]):
                scope = self.async_request_factory._base_scope(
                    path="/", http_version="2.0"
                )
                scope["headers"] = case["headers"]
                request = ASGIRequest(scope, None)
                self.assertEqual(request.META["HTTP_COOKIE"], "a=abc; b=def; c=ghi")
                self.assertEqual(request.COOKIES, {"a": "abc", "b": "def", "c": "ghi"})