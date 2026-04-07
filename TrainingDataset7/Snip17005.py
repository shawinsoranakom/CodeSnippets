def test_aggregation_nested_subquery_outerref(self):
        publisher_with_same_name = Publisher.objects.filter(
            id__in=Subquery(
                Publisher.objects.filter(
                    name=OuterRef(OuterRef("publisher__name")),
                ).values("id"),
            ),
        ).values(publisher_count=Count("id"))[:1]
        books_breakdown = Book.objects.annotate(
            publisher_count=Subquery(publisher_with_same_name),
            authors_count=Count("authors"),
        ).values_list("publisher_count", flat=True)
        self.assertSequenceEqual(books_breakdown, [1] * 6)