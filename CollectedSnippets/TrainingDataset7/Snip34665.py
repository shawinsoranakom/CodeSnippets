def test_request_factory_query_params(self):
        tests = (
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
            "trace",
        )
        for method in tests:
            with self.subTest(method=method):
                factory = getattr(self.request_factory, method)
                request = factory(
                    "/somewhere", query_params={"example": "data", "empty": []}
                )
                self.assertEqual(request.GET["example"], "data")
                self.assertNotIn("empty", request.GET)