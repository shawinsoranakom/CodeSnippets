def test_filter_in_subquery_or_aggregation(self):
        """
        Filtering against an aggregate requires the usage of the HAVING clause.

        If such a filter is unionized to a non-aggregate one the latter will
        also need to be moved to the HAVING clause and have its grouping
        columns used in the GROUP BY.

        When this is done with a subquery the specialized logic in charge of
        using outer reference columns to group should be used instead of the
        subquery itself as the latter might return multiple rows.
        """
        authors = Author.objects.annotate(
            Count("book"),
        ).filter(Q(book__count__gt=0) | Q(pk__in=Book.objects.values("authors")))
        self.assertCountEqual(authors, Author.objects.all())