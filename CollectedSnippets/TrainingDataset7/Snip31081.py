def test_non_ascii_POST(self):
        payload = FakePayload(urlencode({"key": "España"}))
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_LENGTH": len(payload),
                "CONTENT_TYPE": "application/x-www-form-urlencoded",
                "wsgi.input": payload,
            }
        )
        self.assertEqual(request.POST, {"key": ["España"]})