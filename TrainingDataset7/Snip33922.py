def test_querystring_empty_params(self):
        cases = [{}, QueryDict()]
        request = self.request_factory.get("/")
        qs = "?a=b"
        request_with_qs = self.request_factory.get(f"/{qs}")
        for param in cases:
            # Empty `query_dict` and nothing on `request.GET`.
            with self.subTest(param=param):
                context = RequestContext(request, {"qd": param})
                self.assertRenderEqual(
                    "querystring_empty_params", context, expected="?"
                )
            # Empty `query_dict` and a query string in `request.GET`.
            with self.subTest(param=param, qs=qs):
                context = RequestContext(request_with_qs, {"qd": param})
                expected = "?" if param is not None else qs
                self.assertRenderEqual("querystring_empty_params", context, expected)