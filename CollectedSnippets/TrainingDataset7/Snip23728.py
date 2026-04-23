def test_month_view_without_month_in_url(self):
        res = self.client.get("/dates/books/without_month/2008/")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.context["exception"], "No month specified")