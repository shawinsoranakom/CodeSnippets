def test_accept_headers(self):
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = (
            "text/*,text/html, application/xhtml+xml,application/xml ;q=0.9,*/*;q=0.8,"
        )
        self.assertEqual(
            [str(accepted_type) for accepted_type in request.accepted_types],
            [
                "text/html",
                "application/xhtml+xml",
                "text/*",
                "application/xml; q=0.9",
                "*/*; q=0.8",
            ],
        )
        self.assertEqual(
            [
                str(accepted_type)
                for accepted_type in request.accepted_types_by_precedence
            ],
            [
                "text/html",
                "application/xhtml+xml",
                "application/xml; q=0.9",
                "text/*",
                "*/*; q=0.8",
            ],
        )