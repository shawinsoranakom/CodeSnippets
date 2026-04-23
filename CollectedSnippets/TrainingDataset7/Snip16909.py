def test_double_filtered_aggregates(self):
        agg = Sum("age", filter=Q(Q(name="test2") & ~Q(name="test")))
        self.assertEqual(Author.objects.aggregate(age=agg)["age"], 60)