def test_any_value_filter(self):
        books_qs = (
            Book.objects.values(greatest_pages=Greatest("pages", 600))
            .annotate(
                pubdate_year=AnyValue("pubdate__year", filter=Q(rating__lte=4.5)),
            )
            .values_list("pubdate_year", flat=True)
        )
        self.assertCountEqual(books_qs, [2007, 1995, None])