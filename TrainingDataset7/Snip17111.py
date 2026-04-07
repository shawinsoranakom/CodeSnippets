def test_annotate_with_dates(self):
        # Regression for #10248 - Annotations work with dates()
        qs = (
            Book.objects.annotate(num_authors=Count("authors"))
            .filter(num_authors=2)
            .dates("pubdate", "day")
        )
        self.assertSequenceEqual(
            qs,
            [
                datetime.date(1995, 1, 15),
                datetime.date(2007, 12, 6),
            ],
        )