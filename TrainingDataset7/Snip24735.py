def test_no_response(self):
        msg = (
            "The view %s didn't return an HttpResponse object. It returned None "
            "instead."
        )
        tests = (
            ("/no_response_fbv/", "handlers.views.no_response"),
            ("/no_response_cbv/", "handlers.views.NoResponse.__call__"),
        )
        for url, view in tests:
            with (
                self.subTest(url=url),
                self.assertRaisesMessage(ValueError, msg % view),
            ):
                self.client.get(url)