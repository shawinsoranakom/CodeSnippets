def test_excluded_aggregates(self):
        agg = Sum("age", filter=~Q(name="test2"))
        self.assertEqual(Author.objects.aggregate(age=agg)["age"], 140)