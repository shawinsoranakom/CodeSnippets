def test_querystring_replace(self):
        request = self.request_factory.get("/", {"x": "y", "a": "b"})
        context = RequestContext(request)
        self.assertRenderEqual("querystring_replace", context, expected="?x=y&amp;a=1")