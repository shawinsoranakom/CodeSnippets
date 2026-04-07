def test_set_encoding_clears_GET(self):
        payload = FakePayload("")
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "GET",
                "wsgi.input": payload,
                "QUERY_STRING": "name=Hello%20G%C3%BCnter",
            }
        )
        self.assertEqual(request.GET, {"name": ["Hello Günter"]})
        request.encoding = "iso-8859-16"
        self.assertEqual(request.GET, {"name": ["Hello G\u0102\u0152nter"]})