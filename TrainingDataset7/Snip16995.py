def test_aggregation_subquery_annotation_multivalued(self):
        """
        Subquery annotations must be included in the GROUP BY if they use
        potentially multivalued relations (contain the LOOKUP_SEP).
        """
        subquery_qs = Author.objects.filter(
            pk=OuterRef("pk"),
            book__name=OuterRef("book__name"),
        ).values("pk")
        author_qs = Author.objects.annotate(
            subquery_id=Subquery(subquery_qs),
        ).annotate(count=Count("book"))
        self.assertEqual(author_qs.count(), Author.objects.count())