def test_non_zero_content_length_set_head_request(self):
        hello_world_body = b"<!DOCTYPE html><html><body>Hello World</body></html>"
        content_length = len(hello_world_body)

        def test_app(environ, start_response):
            """
            A WSGI app that returns a hello world with non-zero Content-Length.
            """
            start_response("200 OK", [("Content-length", str(content_length))])
            return [hello_world_body]

        rfile = BytesIO(b"HEAD / HTTP/1.0\r\n")
        rfile.seek(0)

        wfile = UnclosableBytesIO()

        def makefile(mode, *a, **kw):
            if mode == "rb":
                return rfile
            elif mode == "wb":
                return wfile

        request = Stub(makefile=makefile)
        server = Stub(base_environ={}, get_app=lambda: test_app)

        # Prevent logging from appearing in test output.
        with self.assertLogs("django.server", "INFO"):
            # Instantiating a handler runs the request as side effect.
            WSGIRequestHandler(request, "192.168.0.2", server)

        wfile.seek(0)
        lines = list(wfile.readlines())
        body = lines[-1]
        # The body is not returned in a HEAD response.
        self.assertEqual(body, b"\r\n")
        # Non-zero Content-Length is not removed.
        self.assertEqual(lines[-2], f"Content-length: {content_length}\r\n".encode())
        self.assertNotIn(b"Connection: close\r\n", lines)