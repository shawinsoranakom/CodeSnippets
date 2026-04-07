def test_archive_view(self):
        res = self.client.get("/dates/books/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            list(res.context["date_list"]),
            list(Book.objects.dates("pubdate", "year", "DESC")),
        )
        self.assertEqual(list(res.context["latest"]), list(Book.objects.all()))
        self.assertTemplateUsed(res, "generic_views/book_archive.html")