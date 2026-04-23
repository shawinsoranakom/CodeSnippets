def test_querystring_multiple(self):
        request = self.request_factory.get("/", {"x": "y", "a": "b"})
        context = RequestContext(request)
        self.assertRenderEqual("querystring_multiple", context, expected="?x=y&amp;a=b")