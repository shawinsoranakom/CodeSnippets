def test_POST_binary_only(self):
        payload = b"\r\n\x01\x00\x00\x00ab\x00\x00\xcd\xcc,@"
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "application/octet-stream",
            "CONTENT_LENGTH": len(payload),
            "wsgi.input": BytesIO(payload),
        }
        request = WSGIRequest(environ)
        self.assertEqual(request.POST, {})
        self.assertEqual(request.FILES, {})
        self.assertEqual(request.body, payload)

        # Same test without specifying content-type
        environ.update({"CONTENT_TYPE": "", "wsgi.input": BytesIO(payload)})
        request = WSGIRequest(environ)
        self.assertEqual(request.POST, {})
        self.assertEqual(request.FILES, {})
        self.assertEqual(request.body, payload)