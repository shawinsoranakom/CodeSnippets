def test_follow_307_and_308_redirect(self):
        """
        A 307 or 308 redirect preserves the request method after the redirect.
        """
        methods = ("get", "post", "head", "options", "put", "patch", "delete", "trace")
        codes = (307, 308)
        for method, code in itertools.product(methods, codes):
            with self.subTest(method=method, code=code):
                req_method = getattr(self.client, method)
                response = req_method(
                    "/redirect_view_%s/" % code, data={"value": "test"}, follow=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.request["PATH_INFO"], "/post_view/")
                self.assertEqual(response.request["REQUEST_METHOD"], method.upper())