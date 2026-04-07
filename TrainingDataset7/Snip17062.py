def test_aggregate_reference_lookup_rhs(self):
        aggregates = Author.objects.annotate(
            max_book_author=Max("book__authors"),
        ).aggregate(count=Count("id", filter=Q(id=F("max_book_author"))))
        self.assertEqual(aggregates, {"count": 1})