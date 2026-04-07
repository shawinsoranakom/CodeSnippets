def test_repr(self):
        r = StreamingHttpResponse(iter(["hello", "café"]))
        self.assertEqual(
            repr(r),
            '<StreamingHttpResponse status_code=200, "text/html; charset=utf-8">',
        )