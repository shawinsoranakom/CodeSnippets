def test_dates_with_aggregation(self):
        """
        .dates() returns a distinct set of dates when applied to a
        QuerySet with aggregation.

        Refs #18056. Previously, .dates() would return distinct (date_kind,
        aggregation) sets, in this case (year, num_authors), so 2008 would be
        returned twice because there are books from 2008 with a different
        number of authors.
        """
        dates = Book.objects.annotate(num_authors=Count("authors")).dates(
            "pubdate", "year"
        )
        self.assertSequenceEqual(
            dates,
            [
                datetime.date(1991, 1, 1),
                datetime.date(1995, 1, 1),
                datetime.date(2007, 1, 1),
                datetime.date(2008, 1, 1),
            ],
        )