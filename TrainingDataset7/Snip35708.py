def test_re_path(self):
        match = resolve("/regex/1/")
        self.assertEqual(match.url_name, "regex")
        self.assertEqual(match.kwargs, {"pk": "1"})
        self.assertEqual(match.route, "^regex/(?P<pk>[0-9]+)/$")
        self.assertEqual(match.captured_kwargs, {"pk": "1"})
        self.assertEqual(match.extra_kwargs, {})