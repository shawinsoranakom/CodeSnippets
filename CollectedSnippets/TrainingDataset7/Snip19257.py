def test_patch_vary_headers(self):
        headers = (
            # Initial vary, new headers, resulting vary.
            (None, ("Accept-Encoding",), "Accept-Encoding"),
            ("Accept-Encoding", ("accept-encoding",), "Accept-Encoding"),
            ("Accept-Encoding", ("ACCEPT-ENCODING",), "Accept-Encoding"),
            ("Cookie", ("Accept-Encoding",), "Cookie, Accept-Encoding"),
            (
                "Cookie, Accept-Encoding",
                ("Accept-Encoding",),
                "Cookie, Accept-Encoding",
            ),
            (
                "Cookie, Accept-Encoding",
                ("Accept-Encoding", "cookie"),
                "Cookie, Accept-Encoding",
            ),
            (None, ("Accept-Encoding", "COOKIE"), "Accept-Encoding, COOKIE"),
            (
                "Cookie,     Accept-Encoding",
                ("Accept-Encoding", "cookie"),
                "Cookie, Accept-Encoding",
            ),
            (
                "Cookie    ,     Accept-Encoding",
                ("Accept-Encoding", "cookie"),
                "Cookie, Accept-Encoding",
            ),
        )
        for initial_vary, newheaders, resulting_vary in headers:
            with self.subTest(initial_vary=initial_vary, newheaders=newheaders):
                template = engines["django"].from_string("This is a test")
                response = TemplateResponse(HttpRequest(), template)
                if initial_vary is not None:
                    response.headers["Vary"] = initial_vary
                patch_vary_headers(response, newheaders)
                self.assertEqual(response.headers["Vary"], resulting_vary)