async def test_request_limited_read(self):
        tests = ["GET", "POST"]
        for method in tests:
            with self.subTest(method=method):
                request = self.request_factory.generic(
                    method,
                    "/somewhere",
                )
                self.assertEqual(request.read(200), b"")