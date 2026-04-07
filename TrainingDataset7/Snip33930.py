def test_querystring_variable(self):
        request = self.request_factory.get("/")
        context = RequestContext(request, {"a": 1})
        self.assertRenderEqual("querystring_variable", context, expected="?a=1")