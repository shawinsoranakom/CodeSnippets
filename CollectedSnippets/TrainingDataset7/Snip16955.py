def test_aggregate_annotation(self):
        vals = Book.objects.annotate(num_authors=Count("authors__id")).aggregate(
            Avg("num_authors")
        )
        self.assertEqual(vals, {"num_authors__avg": Approximate(1.66, places=1)})