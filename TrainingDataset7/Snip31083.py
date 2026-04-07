def test_utf8_charset_POST(self):
        for charset in ["utf-8", "UTF-8"]:
            with self.subTest(charset=charset):
                payload = FakePayload(urlencode({"key": "España"}))
                request = WSGIRequest(
                    {
                        "REQUEST_METHOD": "POST",
                        "CONTENT_LENGTH": len(payload),
                        "CONTENT_TYPE": (
                            f"application/x-www-form-urlencoded; charset={charset}"
                        ),
                        "wsgi.input": payload,
                    }
                )
                self.assertEqual(request.POST, {"key": ["España"]})