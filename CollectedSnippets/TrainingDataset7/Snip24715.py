def test_non_ascii_query_string(self):
        """
        Non-ASCII query strings are properly decoded (#20530, #22996).
        """
        environ = self.request_factory.get("/").environ
        raw_query_strings = [
            b"want=caf%C3%A9",  # This is the proper way to encode 'café'
            b"want=caf\xc3\xa9",  # UA forgot to quote bytes
            b"want=caf%E9",  # UA quoted, but not in UTF-8
            # UA forgot to convert Latin-1 to UTF-8 and to quote (typical of
            # MSIE).
            b"want=caf\xe9",
        ]
        got = []
        for raw_query_string in raw_query_strings:
            # Simulate http.server.BaseHTTPRequestHandler.parse_request
            # handling of raw request.
            environ["QUERY_STRING"] = str(raw_query_string, "iso-8859-1")
            request = WSGIRequest(environ)
            got.append(request.GET["want"])
        # %E9 is converted to the Unicode replacement character by parse_qsl
        self.assertEqual(got, ["café", "café", "caf\ufffd", "café"])