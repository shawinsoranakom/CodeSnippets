def test_querystring_remove_querydict(self):
        request = self.request_factory.get("/", {"x": "1"})
        my_qd = QueryDict(mutable=True)
        my_qd["x"] = None
        context = RequestContext(
            request, {"request": request.GET, "my_query_dict": my_qd}
        )
        self.assertRenderEqual("querystring_remove_querydict", context, expected="?")