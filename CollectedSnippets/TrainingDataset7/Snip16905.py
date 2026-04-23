def test_filtered_aggregates(self):
        agg = Sum("age", filter=Q(name__startswith="test"))
        self.assertEqual(Author.objects.aggregate(age=agg)["age"], 200)