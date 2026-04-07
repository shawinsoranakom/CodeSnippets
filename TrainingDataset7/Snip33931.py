def test_querystring_dict(self):
        context = {"my_dict": {"a": 1}}
        self.assertRenderEqual("querystring_dict", context, expected="?a=1")