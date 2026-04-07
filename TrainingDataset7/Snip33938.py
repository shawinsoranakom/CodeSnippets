def test_querystring_add_list(self):
        request = self.request_factory.get("/")
        context = RequestContext(request, {"my_list": [2, 3]})
        self.assertRenderEqual("querystring_list", context, expected="?a=2&amp;a=3")