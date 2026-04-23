def test_date_detail_by_slug(self):
        res = self.client.get("/dates/books/2006/may/01/byslug/dreaming-in-code/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["book"], Book.objects.get(slug="dreaming-in-code"))