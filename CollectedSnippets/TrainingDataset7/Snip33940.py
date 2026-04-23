def test_querystring_with_explicit_query_dict(self):
        request = self.request_factory.get("/", {"a": 1})
        self.assertRenderEqual(
            "querystring_query_dict", {"request": request}, expected="?a=2"
        )