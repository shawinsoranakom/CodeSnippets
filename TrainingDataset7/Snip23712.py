def test_year_view_invalid_pattern(self):
        res = self.client.get("/dates/books/no_year/")
        self.assertEqual(res.status_code, 404)