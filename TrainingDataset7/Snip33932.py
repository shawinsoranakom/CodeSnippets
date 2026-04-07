def test_querystring_dict_list_values(self):
        context = {"my_dict": {"a": [1, 2]}}
        self.assertRenderEqual(
            "querystring_dict_list", context, expected="?a=1&amp;a=2"
        )