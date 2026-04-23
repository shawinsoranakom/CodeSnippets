def test_year_view_paginated(self):
        res = self.client.get("/dates/books/2006/paginated/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            list(res.context["book_list"]),
            list(Book.objects.filter(pubdate__year=2006)),
        )
        self.assertEqual(
            list(res.context["object_list"]),
            list(Book.objects.filter(pubdate__year=2006)),
        )
        self.assertTemplateUsed(res, "generic_views/book_archive_year.html")