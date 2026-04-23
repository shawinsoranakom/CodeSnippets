def test_post_like_requests(self):
        # A POST-like request can pass a query string as data
        response = self.client.post("/request_data/", data={"foo": "whiz"})
        self.assertIsNone(response.context["get-foo"])
        self.assertEqual(response.context["post-foo"], "whiz")

        # A POST-like request can pass a query string as part of the URL
        response = self.client.post("/request_data/?foo=whiz")
        self.assertEqual(response.context["get-foo"], "whiz")
        self.assertIsNone(response.context["post-foo"])

        response = self.client.post("/request_data/", query_params={"foo": "whiz"})
        self.assertEqual(response.context["get-foo"], "whiz")
        self.assertIsNone(response.context["post-foo"])

        # POST data provided in the URL augments actual form data
        response = self.client.post("/request_data/?foo=whiz", data={"foo": "bang"})
        self.assertEqual(response.context["get-foo"], "whiz")
        self.assertEqual(response.context["post-foo"], "bang")

        response = self.client.post("/request_data/?foo=whiz", data={"bar": "bang"})
        self.assertEqual(response.context["get-foo"], "whiz")
        self.assertIsNone(response.context["get-bar"])
        self.assertIsNone(response.context["post-foo"])
        self.assertEqual(response.context["post-bar"], "bang")