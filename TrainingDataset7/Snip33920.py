def test_querystring_multiple_lists(self):
        request = self.request_factory.get("/", {"x": ["y", "z"], "a": ["b", "c"]})
        context = RequestContext(request)
        expected = "?x=y&amp;x=z&amp;a=b&amp;a=c"
        self.assertRenderEqual("querystring_multiple_lists", context, expected=expected)