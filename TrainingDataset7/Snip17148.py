def test_aggregate_on_relation(self):
        # A query with an existing annotation aggregation on a relation should
        # succeed.
        qs = Book.objects.annotate(avg_price=Avg("price")).aggregate(
            publisher_awards=Sum("publisher__num_awards")
        )
        self.assertEqual(qs["publisher_awards"], 30)