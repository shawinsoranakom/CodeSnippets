def test_querystring_non_string_dict_keys(self):
        context = {"my_dict": {0: 1}}
        msg = "querystring requires strings for mapping keys (got 0 instead)."
        self.assertTemplateSyntaxError("querystring_non_string_dict_keys", context, msg)