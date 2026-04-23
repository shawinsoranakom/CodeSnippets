def test_wsgirequest_with_force_script_name(self):
        """
        The FORCE_SCRIPT_NAME setting takes precedence over the request's
        SCRIPT_NAME environment parameter (#20169).
        """
        with override_settings(FORCE_SCRIPT_NAME="/FORCED_PREFIX/"):
            request = WSGIRequest(
                {
                    "PATH_INFO": "/somepath/",
                    "SCRIPT_NAME": "/PREFIX/",
                    "REQUEST_METHOD": "get",
                    "wsgi.input": BytesIO(b""),
                }
            )
            self.assertEqual(request.path, "/FORCED_PREFIX/somepath/")