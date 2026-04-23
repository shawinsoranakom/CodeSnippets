def test_path_lookup_with_empty_string_inclusion(self):
        match = resolve("/more/99/")
        self.assertEqual(match.url_name, "inner-more")
        self.assertEqual(match.route, r"^more/(?P<extra>\w+)/$")
        self.assertEqual(match.kwargs, {"extra": "99", "sub-extra": True})
        self.assertEqual(match.captured_kwargs, {"extra": "99"})
        self.assertEqual(match.extra_kwargs, {"sub-extra": True})