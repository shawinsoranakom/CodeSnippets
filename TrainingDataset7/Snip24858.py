def test_headers_bytestring(self):
        response = HttpResponse()
        response["X-Foo"] = b"bar"
        self.assertEqual(response["X-Foo"], "bar")
        self.assertEqual(response.headers["X-Foo"], "bar")