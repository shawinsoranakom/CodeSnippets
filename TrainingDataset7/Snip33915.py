def test_querystring_empty_get_params(self):
        context = RequestContext(self.request_factory.get("/"))
        self.assertRenderEqual("querystring_empty_get_params", context, expected="?")