def test_gone_response_logged(self):
        for path, escaped in [
            ("/foo/", "/foo/"),
            (r"/%1B[1;31mNOW IN RED!!!1B[0m/", r"/\x1b[1;31mNOW IN RED!!!1B[0m/"),
        ]:
            with self.subTest(path=path):
                request = self.rf.get(path)
                with self.assertLogs("django.request", "WARNING") as handler:
                    RedirectView().dispatch(request)

                self.assertLogRecord(
                    handler, f"Gone: {escaped}", logging.WARNING, 410, request
                )