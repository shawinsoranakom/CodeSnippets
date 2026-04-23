def test_querystring_remove_querydict_many(self):
        request = self.request_factory.get(
            "/", {"test": ["value1", "value2"], "a": [1, 2]}
        )

        qd_none = QueryDict(mutable=True)
        qd_none["test"] = None

        qd_list_none = QueryDict(mutable=True)
        qd_list_none.setlist("test", [None, None])

        qd_empty_list = QueryDict(mutable=True)
        qd_empty_list.setlist("test", [])

        for qd in (qd_none, qd_list_none, qd_empty_list):
            with self.subTest(my_query_dict=qd):
                context = RequestContext(
                    request, {"request": request.GET, "my_query_dict": qd}
                )
                self.assertRenderEqual(
                    "querystring_remove_querydict_many",
                    context,
                    expected="?a=1&amp;a=2",
                )