def test_wsgirequest_script_url_double_slashes(self):
        """
        WSGI squashes multiple successive slashes in PATH_INFO, WSGIRequest
        should take that into account when populating request.path and
        request.META['SCRIPT_NAME'] (#17133).
        """
        request = WSGIRequest(
            {
                "SCRIPT_URL": "/mst/milestones//accounts/login//help",
                "PATH_INFO": "/milestones/accounts/login/help",
                "REQUEST_METHOD": "get",
                "wsgi.input": BytesIO(b""),
            }
        )
        self.assertEqual(request.path, "/mst/milestones/accounts/login/help")
        self.assertEqual(request.META["SCRIPT_NAME"], "/mst")