def test_querystring_remove(self):
        request = self.request_factory.get("/", {"test": "value", "a": "1"})
        context = RequestContext(request)
        self.assertRenderEqual("querystring_remove", context, expected="?a=1")