def test_querystring_add(self):
        request = self.request_factory.get("/", {"a": "b"})
        context = RequestContext(request)
        self.assertRenderEqual(
            "querystring_add", context, expected="?a=b&amp;test_new=something"
        )