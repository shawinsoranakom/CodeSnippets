def test_aggregate_combined_queries(self):
        # Combined queries could have members in their values select mask while
        # others have them in their annotation mask which makes annotation
        # pruning complex to implement hence why it's not implemented.
        qs = Author.objects.values(
            "age",
            other=Value(0),
        ).union(
            Book.objects.values(
                age=Value(0),
                other=Value(0),
            )
        )
        self.assertEqual(qs.count(), 3)