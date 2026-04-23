def test_path_lookup_with_extra_kwarg(self):
        match = resolve("/books/2007/")
        self.assertEqual(match.url_name, "books-2007")
        self.assertEqual(match.args, ())
        self.assertEqual(match.kwargs, {"extra": True})
        self.assertEqual(match.route, "books/2007/")
        self.assertEqual(match.captured_kwargs, {})
        self.assertEqual(match.extra_kwargs, {"extra": True})