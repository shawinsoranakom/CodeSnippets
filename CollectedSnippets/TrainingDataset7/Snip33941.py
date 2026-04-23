def test_querystring_with_explicit_query_dict_and_no_request(self):
        context = {"my_query_dict": QueryDict("a=1&b=2")}
        self.assertRenderEqual(
            "querystring_query_dict_no_request", context, expected="?a=2&amp;b=2"
        )