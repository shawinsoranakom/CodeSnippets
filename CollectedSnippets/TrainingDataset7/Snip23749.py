def test_today_view(self):
        res = self.client.get("/dates/books/today/")
        self.assertEqual(res.status_code, 404)
        res = self.client.get("/dates/books/today/allow_empty/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["day"], datetime.date.today())