def test_empty_filtered_aggregates(self):
        agg = Count("pk", filter=Q())
        self.assertEqual(Author.objects.aggregate(count=agg)["count"], 3)