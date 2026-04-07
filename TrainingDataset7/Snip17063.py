def test_aggregate_reference_lookup_rhs_iter(self):
        aggregates = Author.objects.annotate(
            max_book_author=Max("book__authors"),
        ).aggregate(count=Count("id", filter=Q(id__in=[F("max_book_author"), 0])))
        self.assertEqual(aggregates, {"count": 1})