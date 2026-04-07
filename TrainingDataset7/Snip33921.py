def test_querystring_lists_with_replacement(self):
        request = self.request_factory.get("/", {"x": ["y", "z"], "a": ["b", "c"]})
        context = RequestContext(request)
        expected = "?x=y&amp;x=z&amp;a=1"
        self.assertRenderEqual(
            "querystring_lists_with_replacement", context, expected=expected
        )