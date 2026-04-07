def test_invalid_multipart_boundary(self):
        """
        Invalid boundary string should produce a "Bad Request" response, not a
        server error (#23887).
        """
        environ = self.request_factory.post("/malformed_post/").environ
        environ["CONTENT_TYPE"] = "multipart/form-data; boundary=WRONG\x07"
        handler = WSGIHandler()
        response = handler(environ, lambda *a, **k: None)
        # Expect "bad request" response
        self.assertEqual(response.status_code, 400)