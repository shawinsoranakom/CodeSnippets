def test_week_view_paginated(self):
        week_start = datetime.date(2008, 9, 28)
        week_end = week_start + datetime.timedelta(days=7)
        res = self.client.get("/dates/books/2008/week/39/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            list(res.context["book_list"]),
            list(Book.objects.filter(pubdate__gte=week_start, pubdate__lt=week_end)),
        )
        self.assertEqual(
            list(res.context["object_list"]),
            list(Book.objects.filter(pubdate__gte=week_start, pubdate__lt=week_end)),
        )
        self.assertTemplateUsed(res, "generic_views/book_archive_week.html")