def test_path_reverse_with_parameter(self):
        url = reverse(
            "articles-year-month-day", kwargs={"year": 2015, "month": 4, "day": 12}
        )
        self.assertEqual(url, "/articles/2015/4/12/")