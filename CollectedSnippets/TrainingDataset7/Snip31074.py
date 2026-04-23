def test_wsgirequest_path_info(self):
        def wsgi_str(path_info, encoding="utf-8"):
            path_info = path_info.encode(
                encoding
            )  # Actual URL sent by the browser (bytestring)
            path_info = path_info.decode(
                "iso-8859-1"
            )  # Value in the WSGI environ dict (native string)
            return path_info

        # Regression for #19468
        request = WSGIRequest(
            {
                "PATH_INFO": wsgi_str("/سلام/"),
                "REQUEST_METHOD": "get",
                "wsgi.input": BytesIO(b""),
            }
        )
        self.assertEqual(request.path, "/سلام/")

        # The URL may be incorrectly encoded in a non-UTF-8 encoding (#26971)
        request = WSGIRequest(
            {
                "PATH_INFO": wsgi_str("/café/", encoding="iso-8859-1"),
                "REQUEST_METHOD": "get",
                "wsgi.input": BytesIO(b""),
            }
        )
        # Since it's impossible to decide the (wrong) encoding of the URL, it's
        # left percent-encoded in the path.
        self.assertEqual(request.path, "/caf%E9/")