def test_day_view_invalid_pattern(self):
        res = self.client.get("/dates/books/2007/oct/no_day/")
        self.assertEqual(res.status_code, 404)