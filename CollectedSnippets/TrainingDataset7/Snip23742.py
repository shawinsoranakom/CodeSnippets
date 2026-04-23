def test_day_view(self):
        res = self.client.get("/dates/books/2008/oct/01/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "generic_views/book_archive_day.html")
        self.assertEqual(
            list(res.context["book_list"]),
            list(Book.objects.filter(pubdate=datetime.date(2008, 10, 1))),
        )
        self.assertEqual(res.context["day"], datetime.date(2008, 10, 1))

        # Since allow_empty=False, next/prev days must be valid.
        self.assertIsNone(res.context["next_day"])
        self.assertEqual(res.context["previous_day"], datetime.date(2006, 5, 1))