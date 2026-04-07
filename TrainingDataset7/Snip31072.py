def test_wsgirequest_path_with_force_script_name_trailing_slash(self):
        """
        The request's path is correctly assembled, regardless of whether or not
        the FORCE_SCRIPT_NAME setting has a trailing slash (#20169).
        """
        # With trailing slash
        with override_settings(FORCE_SCRIPT_NAME="/FORCED_PREFIX/"):
            request = WSGIRequest(
                {
                    "PATH_INFO": "/somepath/",
                    "REQUEST_METHOD": "get",
                    "wsgi.input": BytesIO(b""),
                }
            )
            self.assertEqual(request.path, "/FORCED_PREFIX/somepath/")
        # Without trailing slash
        with override_settings(FORCE_SCRIPT_NAME="/FORCED_PREFIX"):
            request = WSGIRequest(
                {
                    "PATH_INFO": "/somepath/",
                    "REQUEST_METHOD": "get",
                    "wsgi.input": BytesIO(b""),
                }
            )
            self.assertEqual(request.path, "/FORCED_PREFIX/somepath/")