def test_no_body_returned_for_head_requests(self):
        hello_world_body = b"<!DOCTYPE html><html><body>Hello World</body></html>"
        content_length = len(hello_world_body)

        def test_app(environ, start_response):
            """A WSGI app that returns a hello world."""
            start_response("200 OK", [])
            return [hello_world_body]

        rfile = BytesIO(b"GET / HTTP/1.0\r\n")
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
        # The body is returned in a GET response.
        self.assertEqual(body, hello_world_body)
        self.assertIn(f"Content-Length: {content_length}\r\n".encode(), lines)
        self.assertNotIn(b"Connection: close\r\n", lines)

        rfile = BytesIO(b"HEAD / HTTP/1.0\r\n")
        rfile.seek(0)
        wfile = UnclosableBytesIO()

        with self.assertLogs("django.server", "INFO"):
            WSGIRequestHandler(request, "192.168.0.2", server)

        wfile.seek(0)
        lines = list(wfile.readlines())
        body = lines[-1]
        # The body is not returned in a HEAD response.
        self.assertEqual(body, b"\r\n")
        self.assertIs(
            any([line.startswith(b"Content-Length:") for line in lines]), False
        )
        self.assertNotIn(b"Connection: close\r\n", lines)