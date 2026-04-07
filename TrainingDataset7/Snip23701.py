def test_date_list_order(self):
        """date_list should be sorted descending in index"""
        _make_books(5, base_date=datetime.date(2011, 12, 25))
        res = self.client.get("/dates/books/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            list(res.context["date_list"]),
            sorted(res.context["date_list"], reverse=True),
        )