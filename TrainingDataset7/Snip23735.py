def test_week_view_invalid_pattern(self):
        res = self.client.get("/dates/books/2007/week/no_week/")
        self.assertEqual(res.status_code, 404)