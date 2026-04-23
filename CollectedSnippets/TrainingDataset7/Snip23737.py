def test_week_iso_format(self):
        res = self.client.get("/dates/books/2008/week/40/iso_format/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "generic_views/book_archive_week.html")
        self.assertEqual(
            list(res.context["book_list"]),
            [Book.objects.get(pubdate=datetime.date(2008, 10, 1))],
        )
        self.assertEqual(res.context["week"], datetime.date(2008, 9, 29))