def test_querystring_multiple_args_override(self):
        context = {"my_dict": {"x": 0, "y": 42}, "my_query_dict": QueryDict("a=1&b=2")}
        self.assertRenderEqual(
            "querystring_multiple_args_override",
            context,
            expected="?x=3&amp;a=1&amp;b=2",
        )