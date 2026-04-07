def test_json_serialization(self):
        """The test client serializes JSON data."""
        methods = ("post", "put", "patch", "delete")
        tests = (
            ({"value": 37}, {"value": 37}),
            ([37, True], [37, True]),
            ((37, False), [37, False]),
        )
        for method in methods:
            with self.subTest(method=method):
                for data, expected in tests:
                    with self.subTest(data):
                        client_method = getattr(self.client, method)
                        method_name = method.upper()
                        response = client_method(
                            "/json_view/", data, content_type="application/json"
                        )
                        self.assertContains(response, "Viewing %s page." % method_name)
                        self.assertEqual(response.context["data"], expected)