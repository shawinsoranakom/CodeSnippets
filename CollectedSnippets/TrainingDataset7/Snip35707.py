def test_two_variable_at_start_of_path_pattern(self):
        match = resolve("/en/foo/")
        self.assertEqual(match.url_name, "lang-and-path")
        self.assertEqual(match.kwargs, {"lang": "en", "url": "foo"})
        self.assertEqual(match.route, "<lang>/<path:url>/")
        self.assertEqual(match.captured_kwargs, {"lang": "en", "url": "foo"})
        self.assertEqual(match.extra_kwargs, {})