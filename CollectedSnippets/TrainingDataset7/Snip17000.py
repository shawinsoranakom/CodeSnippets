def test_any_value(self):
        books_qs = (
            Book.objects.values(greatest_pages=Greatest("pages", 600))
            .annotate(
                pubdate_year=AnyValue("pubdate__year"),
            )
            .values_list("pubdate_year", flat=True)
            .order_by("pubdate_year")
        )
        self.assertCountEqual(books_qs[0:2], [1991, 1995])
        self.assertIn(books_qs[2], [2007, 2008])