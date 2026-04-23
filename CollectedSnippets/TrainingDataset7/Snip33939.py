def test_querystring_add_dict(self):
        request = self.request_factory.get("/")
        context = RequestContext(request, {"my_dict": {i: i * 2 for i in range(3)}})
        self.assertRenderEqual(
            "querystring_dict", context, expected="?a=0&amp;a=1&amp;a=2"
        )