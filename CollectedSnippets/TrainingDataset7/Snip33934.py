def test_querystring_request_get_ignored(self):
        cases = [({"y": "x"}, "?y=x"), ({}, "?")]
        request = self.request_factory.get("/", {"x": "y", "a": "b"})
        for param, expected in cases:
            with self.subTest(param=param):
                context = RequestContext(request, {"my_mapping": param})
                self.assertRenderEqual(
                    "querystring_request_get_ignored", context, expected=expected
                )