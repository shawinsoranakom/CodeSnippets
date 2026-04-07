def test_wsgirequest(self):
        request = WSGIRequest(
            {
                "PATH_INFO": "bogus",
                "REQUEST_METHOD": "bogus",
                "CONTENT_TYPE": "text/html; charset=utf8",
                "wsgi.input": BytesIO(b""),
            }
        )
        self.assertEqual(list(request.GET), [])
        self.assertEqual(list(request.POST), [])
        self.assertEqual(list(request.COOKIES), [])
        self.assertEqual(
            set(request.META),
            {
                "PATH_INFO",
                "REQUEST_METHOD",
                "SCRIPT_NAME",
                "CONTENT_TYPE",
                "wsgi.input",
            },
        )
        self.assertEqual(request.META["PATH_INFO"], "bogus")
        self.assertEqual(request.META["REQUEST_METHOD"], "bogus")
        self.assertEqual(request.META["SCRIPT_NAME"], "")
        self.assertEqual(request.content_type, "text/html")
        self.assertEqual(request.content_params, {"charset": "utf8"})