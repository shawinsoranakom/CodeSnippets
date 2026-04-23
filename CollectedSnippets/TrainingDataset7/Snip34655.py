def test_query_params(self):
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
                client_method = getattr(self.client, method)
                response = client_method("/get_view/", query_params={"example": "data"})
                self.assertEqual(response.wsgi_request.GET["example"], "data")