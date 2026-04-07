def test_aggregates_over_annotations(self):
        # Non-ordinal, non-computed Aggregates over annotations correctly
        # inherit the annotation's internal type if the annotation is ordinal
        # or computed
        vals = Book.objects.annotate(num_authors=Count("authors")).aggregate(
            Max("num_authors")
        )
        self.assertEqual(vals, {"num_authors__max": 3})

        vals = Publisher.objects.annotate(avg_price=Avg("book__price")).aggregate(
            Max("avg_price")
        )
        self.assertEqual(vals, {"avg_price__max": 75.0})