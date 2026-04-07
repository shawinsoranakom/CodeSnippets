def test_querystring_remove_nonexistent(self):
        request = self.request_factory.get("/", {"x": "y", "a": "1"})
        context = RequestContext(request)
        self.assertRenderEqual(
            "querystring_remove_nonexistent", context, expected="?x=y&amp;a=1"
        )