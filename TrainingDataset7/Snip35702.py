def test_path_lookup_without_parameters(self):
        match = resolve("/articles/2003/")
        self.assertEqual(match.url_name, "articles-2003")
        self.assertEqual(match.args, ())
        self.assertEqual(match.kwargs, {})
        self.assertEqual(match.route, "articles/2003/")
        self.assertEqual(match.captured_kwargs, {})
        self.assertEqual(match.extra_kwargs, {})