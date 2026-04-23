def test_get_like_requests(self):
        for method_name in ("get", "head"):
            # A GET-like request can pass a query string as data (#10571)
            method = getattr(self.client, method_name)
            response = method("/request_data/", data={"foo": "whiz"})
            self.assertEqual(response.context["get-foo"], "whiz")

            # A GET-like request can pass a query string as part of the URL
            response = method("/request_data/?foo=whiz")
            self.assertEqual(response.context["get-foo"], "whiz")

            # Data provided in the URL to a GET-like request is overridden by
            # actual form data.
            response = method("/request_data/?foo=whiz", data={"foo": "bang"})
            self.assertEqual(response.context["get-foo"], "bang")

            response = method("/request_data/?foo=whiz", data={"bar": "bang"})
            self.assertIsNone(response.context["get-foo"])
            self.assertEqual(response.context["get-bar"], "bang")