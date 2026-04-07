def test_querystring_non_empty_get_params(self):
        request = self.request_factory.get("/", {"a": "b"})
        context = RequestContext(request)
        self.assertRenderEqual(
            "querystring_non_empty_get_params", context, expected="?a=b"
        )