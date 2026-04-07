def test_allow_empty_archive_view(self):
        Book.objects.all().delete()
        res = self.client.get("/dates/books/allow_empty/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["date_list"]), [])
        self.assertTemplateUsed(res, "generic_views/book_archive.html")