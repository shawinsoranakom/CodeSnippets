def test_querystring_remove_all_params(self):
        non_empty_context = RequestContext(self.request_factory.get("/?a=b"))
        empty_context = RequestContext(self.request_factory.get("/"))
        for context in [non_empty_context, empty_context]:
            with self.subTest(context=context):
                self.assertRenderEqual("querystring_remove_all_params", context, "?")