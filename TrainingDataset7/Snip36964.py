def test_request_meta_filtering(self):
        headers = {
            "API_URL": "super secret",
            "A_SIGNATURE_VALUE": "super secret",
            "MY_KEY": "super secret",
            "PASSWORD": "super secret",
            "SECRET_VALUE": "super secret",
            "SOME_TOKEN": "super secret",
            "THE_AUTH": "super secret",
        }
        request = self.rf.get("/", headers=headers)
        reporter_filter = SafeExceptionReporterFilter()
        cleansed_headers = reporter_filter.get_safe_request_meta(request)
        for header in headers:
            with self.subTest(header=header):
                self.assertEqual(
                    cleansed_headers[f"HTTP_{header}"],
                    reporter_filter.cleansed_substitute,
                )
        self.assertEqual(
            cleansed_headers["HTTP_COOKIE"],
            reporter_filter.cleansed_substitute,
        )