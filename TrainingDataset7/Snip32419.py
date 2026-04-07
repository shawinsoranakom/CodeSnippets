async def test_non_http_requests_passed_to_the_wrapped_application(self):
        tests = [
            "/static/path.txt",
            "/non-static/path.txt",
        ]
        for path in tests:
            with self.subTest(path=path):
                scope = {"type": "websocket", "path": path}
                handler = ASGIStaticFilesHandler(MockApplication())
                response = await handler(scope, None, None)
                self.assertEqual(response, "Application called")