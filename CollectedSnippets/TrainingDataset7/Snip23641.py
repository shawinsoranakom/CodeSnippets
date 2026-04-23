def test_method_not_allowed_response_logged(self):
        for path, escaped in [
            ("/foo/", "/foo/"),
            (r"/%1B[1;31mNOW IN RED!!!1B[0m/", r"/\x1b[1;31mNOW IN RED!!!1B[0m/"),
        ]:
            with self.subTest(path=path):
                request = self.rf.get(path, REQUEST_METHOD="BOGUS")
                with self.assertLogs("django.request", "WARNING") as handler:
                    response = SimpleView.as_view()(request)

                self.assertLogRecord(
                    handler,
                    f"Method Not Allowed (BOGUS): {escaped}",
                    logging.WARNING,
                    405,
                    request,
                )
                self.assertEqual(response.status_code, 405)