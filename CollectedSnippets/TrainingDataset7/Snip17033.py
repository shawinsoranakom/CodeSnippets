def test_aggregation_default_not_in_aggregate(self):
        result = Publisher.objects.annotate(
            avg_rating=Avg("book__rating", default=2.5),
        ).aggregate(Sum("num_awards"))
        self.assertEqual(result["num_awards__sum"], 20)