def test_stream_readline(self):
        payload = FakePayload("name=value\nother=string")
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "application/x-www-form-urlencoded",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            },
        )
        self.assertEqual(request.readline(), b"name=value\n")
        self.assertEqual(request.readline(), b"other=string")