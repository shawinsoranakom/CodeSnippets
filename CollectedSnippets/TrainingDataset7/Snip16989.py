def test_aggregation_subquery_annotation(self):
        """Subquery annotations are excluded from the GROUP BY if they are
        not explicitly grouped against."""
        latest_book_pubdate_qs = (
            Book.objects.filter(publisher=OuterRef("pk"))
            .order_by("-pubdate")
            .values("pubdate")[:1]
        )
        publisher_qs = Publisher.objects.annotate(
            latest_book_pubdate=Subquery(latest_book_pubdate_qs),
        ).annotate(count=Count("book"))
        with self.assertNumQueries(1) as ctx:
            list(publisher_qs)
        self.assertEqual(ctx[0]["sql"].count("SELECT"), 2)
        # The GROUP BY should not be by alias either.
        self.assertEqual(ctx[0]["sql"].lower().count("latest_book_pubdate"), 1)