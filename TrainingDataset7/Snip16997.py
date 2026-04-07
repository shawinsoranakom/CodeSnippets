def test_group_by_subquery_annotation(self):
        """
        Subquery annotations are included in the GROUP BY if they are
        grouped against.
        """
        long_books_count_qs = (
            Book.objects.filter(
                publisher=OuterRef("pk"),
                pages__gt=400,
            )
            .values("publisher")
            .annotate(count=Count("pk"))
            .values("count")
        )
        groups = [
            Subquery(long_books_count_qs),
            long_books_count_qs,
            long_books_count_qs.query,
        ]
        for group in groups:
            with self.subTest(group=group.__class__.__name__):
                long_books_count_breakdown = Publisher.objects.values_list(
                    group,
                ).annotate(total=Count("*"))
                self.assertEqual(dict(long_books_count_breakdown), {None: 1, 1: 4})