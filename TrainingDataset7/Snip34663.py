def test_request_factory_default_headers(self):
        request = RequestFactory(
            headers={
                "authorization": "Bearer faketoken",
                "x-another-header": "some other value",
            }
        ).get("/somewhere/")
        self.assertEqual(request.headers["authorization"], "Bearer faketoken")
        self.assertIn("HTTP_AUTHORIZATION", request.META)
        self.assertEqual(request.headers["x-another-header"], "some other value")
        self.assertIn("HTTP_X_ANOTHER_HEADER", request.META)

        request = RequestFactory(
            headers={
                "Authorization": "Bearer faketoken",
                "X-Another-Header": "some other value",
            }
        ).get("/somewhere/")
        self.assertEqual(request.headers["authorization"], "Bearer faketoken")
        self.assertIn("HTTP_AUTHORIZATION", request.META)
        self.assertEqual(request.headers["x-another-header"], "some other value")
        self.assertIn("HTTP_X_ANOTHER_HEADER", request.META)