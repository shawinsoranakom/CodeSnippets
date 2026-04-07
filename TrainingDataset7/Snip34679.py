def test_async_request_factory_default_headers(self):
        request_factory_with_headers = AsyncRequestFactory(
            **{
                "Authorization": "Bearer faketoken",
                "X-Another-Header": "some other value",
            }
        )
        request = request_factory_with_headers.get("/somewhere/")
        self.assertEqual(request.headers["authorization"], "Bearer faketoken")
        self.assertIn("HTTP_AUTHORIZATION", request.META)
        self.assertEqual(request.headers["x-another-header"], "some other value")
        self.assertIn("HTTP_X_ANOTHER_HEADER", request.META)