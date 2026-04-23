def test_date_list_order(self):
        """date_list should be sorted ascending in year view"""
        _make_books(10, base_date=datetime.date(2011, 12, 25))
        res = self.client.get("/dates/books/2011/")
        self.assertEqual(
            list(res.context["date_list"]), sorted(res.context["date_list"])
        )