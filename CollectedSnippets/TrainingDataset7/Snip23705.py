def test_year_view(self):
        res = self.client.get("/dates/books/2008/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["date_list"]), [datetime.date(2008, 10, 1)])
        self.assertEqual(res.context["year"], datetime.date(2008, 1, 1))
        self.assertTemplateUsed(res, "generic_views/book_archive_year.html")

        # Since allow_empty=False, next/prev years must be valid (#7164)
        self.assertIsNone(res.context["next_year"])
        self.assertEqual(res.context["previous_year"], datetime.date(2006, 1, 1))