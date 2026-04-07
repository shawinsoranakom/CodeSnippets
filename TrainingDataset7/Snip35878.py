def test_rereverse(self):
        match = resolve("/resolved/12/")
        self.assertEqual(
            reverse(match.url_name, args=match.args, kwargs=match.kwargs),
            "/resolved/12/",
        )
        match = resolve("/resolved-overridden/12/url/")
        self.assertEqual(
            reverse(match.url_name, args=match.args, kwargs=match.captured_kwargs),
            "/resolved-overridden/12/url/",
        )