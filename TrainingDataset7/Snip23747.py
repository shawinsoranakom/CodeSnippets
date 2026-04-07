def test_custom_month_format(self):
        res = self.client.get("/dates/books/2008/10/01/")
        self.assertEqual(res.status_code, 200)