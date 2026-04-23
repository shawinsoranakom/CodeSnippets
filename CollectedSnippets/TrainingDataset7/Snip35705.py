def test_path_lookup_with_multiple_parameters_and_extra_kwarg(self):
        match = resolve("/books/2015/04/12/")
        self.assertEqual(match.url_name, "books-year-month-day")
        self.assertEqual(match.args, ())
        self.assertEqual(
            match.kwargs, {"year": 2015, "month": 4, "day": 12, "extra": True}
        )
        self.assertEqual(match.route, "books/<int:year>/<int:month>/<int:day>/")
        self.assertEqual(match.captured_kwargs, {"year": 2015, "month": 4, "day": 12})
        self.assertEqual(match.extra_kwargs, {"extra": True})