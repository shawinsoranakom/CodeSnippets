def test_request_methods_with_content(self):
        for method in ["GET", "PUT", "DELETE"]:
            with self.subTest(method=method):
                payload = FakePayload(urlencode({"key": "value"}))
                request = WSGIRequest(
                    {
                        "REQUEST_METHOD": method,
                        "CONTENT_LENGTH": len(payload),
                        "CONTENT_TYPE": "application/x-www-form-urlencoded",
                        "wsgi.input": payload,
                    }
                )
                self.assertEqual(request.POST, {})