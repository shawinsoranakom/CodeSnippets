def test_date_detail_allow_future(self):
        future = datetime.date.today() + datetime.timedelta(days=60)
        urlbit = future.strftime("%Y/%b/%d").lower()
        b = Book.objects.create(
            name="The New New Testement", slug="new-new", pages=600, pubdate=future
        )

        res = self.client.get("/dates/books/%s/new-new/" % urlbit)
        self.assertEqual(res.status_code, 404)

        res = self.client.get("/dates/books/%s/%s/allow_future/" % (urlbit, b.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["book"], b)
        self.assertTemplateUsed(res, "generic_views/book_detail.html")