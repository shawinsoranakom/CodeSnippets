def test_redirect_fetch_redirect_response(self):
        """Preserve extra headers of requests made with django.test.Client."""
        methods = (
            "get",
            "post",
            "head",
            "options",
            "put",
            "patch",
            "delete",
            "trace",
        )
        for method in methods:
            with self.subTest(method=method):
                req_method = getattr(self.client, method)
                # HTTP_REDIRECT in "extra".
                response = req_method(
                    "/redirect_based_on_extra_headers_1/",
                    follow=False,
                    HTTP_REDIRECT="val",
                )
                self.assertRedirects(
                    response,
                    "/redirect_based_on_extra_headers_2/",
                    fetch_redirect_response=True,
                    status_code=302,
                    target_status_code=302,
                )
                # HTTP_REDIRECT in "headers".
                response = req_method(
                    "/redirect_based_on_extra_headers_1/",
                    follow=False,
                    headers={"redirect": "val"},
                )
                self.assertRedirects(
                    response,
                    "/redirect_based_on_extra_headers_2/",
                    fetch_redirect_response=True,
                    status_code=302,
                    target_status_code=302,
                )