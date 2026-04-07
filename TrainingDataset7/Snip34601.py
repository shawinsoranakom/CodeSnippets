def test_follow_307_and_308_get_head_query_string(self):
        methods = ("get", "head")
        codes = (307, 308)
        for method, code in itertools.product(methods, codes):
            with self.subTest(method=method, code=code):
                req_method = getattr(self.client, method)
                response = req_method(
                    "/redirect_view_%s_query_string/" % code,
                    data={"value": "test"},
                    follow=True,
                )
                self.assertRedirects(
                    response, "/post_view/?hello=world", status_code=code
                )
                self.assertEqual(response.request["QUERY_STRING"], "value=test")