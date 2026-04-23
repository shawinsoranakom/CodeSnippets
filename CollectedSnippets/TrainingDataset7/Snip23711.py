def test_year_view_two_custom_sort_orders(self):
        Book.objects.create(
            name="Zebras for Dummies", pages=300, pubdate=datetime.date(2006, 9, 1)
        )
        Book.objects.create(
            name="Hunting Hippos", pages=400, pubdate=datetime.date(2006, 3, 1)
        )
        res = self.client.get("/dates/books/2006/sortedbypageandnamedec/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            list(res.context["date_list"]),
            [
                datetime.date(2006, 3, 1),
                datetime.date(2006, 5, 1),
                datetime.date(2006, 9, 1),
            ],
        )
        self.assertEqual(
            list(res.context["book_list"]),
            list(Book.objects.filter(pubdate__year=2006).order_by("pages", "-name")),
        )
        self.assertEqual(
            list(res.context["object_list"]),
            list(Book.objects.filter(pubdate__year=2006).order_by("pages", "-name")),
        )
        self.assertTemplateUsed(res, "generic_views/book_archive_year.html")