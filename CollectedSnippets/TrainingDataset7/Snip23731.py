def test_week_view(self):
        res = self.client.get("/dates/books/2008/week/39/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "generic_views/book_archive_week.html")
        self.assertEqual(
            res.context["book_list"][0],
            Book.objects.get(pubdate=datetime.date(2008, 10, 1)),
        )
        self.assertEqual(res.context["week"], datetime.date(2008, 9, 28))

        # Since allow_empty=False, next/prev weeks must be valid
        self.assertIsNone(res.context["next_week"])
        self.assertEqual(res.context["previous_week"], datetime.date(2006, 4, 30))