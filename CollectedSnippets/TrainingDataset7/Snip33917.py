def test_querystring_remove_all_params_custom_querydict(self):
        context = {"my_query_dict": QueryDict("a=1&b=2"), "my_dict": {"b": None}}
        self.assertRenderEqual(
            "querystring_remove_all_params_custom_querydict", context, "?"
        )