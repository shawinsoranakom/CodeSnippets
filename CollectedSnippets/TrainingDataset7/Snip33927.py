def test_querystring_remove_from_dict(self):
        request = self.request_factory.get("/", {"test": "value"})
        context = RequestContext(request, {"my_dict": {"test": None}})
        self.assertRenderEqual("querystring_remove_dict", context, expected="?a=1")