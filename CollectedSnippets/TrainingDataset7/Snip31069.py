def test_wsgirequest_with_script_name(self):
        """
        The request's path is correctly assembled, regardless of whether or
        not the SCRIPT_NAME has a trailing slash (#20169).
        """
        # With trailing slash
        request = WSGIRequest(
            {
                "PATH_INFO": "/somepath/",
                "SCRIPT_NAME": "/PREFIX/",
                "REQUEST_METHOD": "get",
                "wsgi.input": BytesIO(b""),
            }
        )
        self.assertEqual(request.path, "/PREFIX/somepath/")
        # Without trailing slash
        request = WSGIRequest(
            {
                "PATH_INFO": "/somepath/",
                "SCRIPT_NAME": "/PREFIX",
                "REQUEST_METHOD": "get",
                "wsgi.input": BytesIO(b""),
            }
        )
        self.assertEqual(request.path, "/PREFIX/somepath/")