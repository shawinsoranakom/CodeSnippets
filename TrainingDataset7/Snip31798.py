def test_strips_underscore_headers(self):
        """WSGIRequestHandler ignores headers containing underscores.

        This follows the lead of nginx and Apache 2.4, and is to avoid
        ambiguity between dashes and underscores in mapping to WSGI environ,
        which can have security implications.
        """

        def test_app(environ, start_response):
            """A WSGI app that just reflects its HTTP environ."""
            start_response("200 OK", [])
            http_environ_items = sorted(
                "%s:%s" % (k, v) for k, v in environ.items() if k.startswith("HTTP_")
            )
            yield (",".join(http_environ_items)).encode()

        rfile = BytesIO()
        rfile.write(b"GET / HTTP/1.0\r\n")
        rfile.write(b"Some-Header: good\r\n")
        rfile.write(b"Some_Header: bad\r\n")
        rfile.write(b"Other_Header: bad\r\n")
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
            # instantiating a handler runs the request as side effect
            WSGIRequestHandler(request, "192.168.0.2", server)

        wfile.seek(0)
        body = list(wfile.readlines())[-1]

        self.assertEqual(body, b"HTTP_SOME_HEADER:good")