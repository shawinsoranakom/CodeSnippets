def test_request_factory_sets_headers(self):
        for method_name, view in self.http_methods_and_views:
            method = getattr(self.request_factory, method_name)
            request = method(
                "/somewhere/",
                headers={
                    "authorization": "Bearer faketoken",
                    "x-another-header": "some other value",
                },
            )
            self.assertEqual(request.headers["authorization"], "Bearer faketoken")
            self.assertIn("HTTP_AUTHORIZATION", request.META)
            self.assertEqual(request.headers["x-another-header"], "some other value")
            self.assertIn("HTTP_X_ANOTHER_HEADER", request.META)

            request = method(
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