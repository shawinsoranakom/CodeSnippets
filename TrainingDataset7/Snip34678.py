def test_request_factory_sets_headers(self):
        request = self.request_factory.get(
            "/somewhere/",
            AUTHORIZATION="Bearer faketoken",
            X_ANOTHER_HEADER="some other value",
        )
        self.assertEqual(request.headers["authorization"], "Bearer faketoken")
        self.assertIn("HTTP_AUTHORIZATION", request.META)
        self.assertEqual(request.headers["x-another-header"], "some other value")
        self.assertIn("HTTP_X_ANOTHER_HEADER", request.META)

        request = self.request_factory.get(
            "/somewhere/",
            headers={
                "Authorization": "Bearer faketoken",
                "X-Another-Header": "some other value",
            },
        )
        self.assertEqual(request.headers["authorization"], "Bearer faketoken")
        self.assertIn("HTTP_AUTHORIZATION", request.META)
        self.assertEqual(request.headers["x-another-header"], "some other value")
        self.assertIn("HTTP_X_ANOTHER_HEADER", request.META)