def test_filtered_numerical_aggregates(self):
        for aggregate, expected_result in (
            (Avg, Approximate(66.7, 1)),
            (StdDev, Approximate(24.9, 1)),
            (Variance, Approximate(622.2, 1)),
        ):
            with self.subTest(aggregate=aggregate.__name__):
                agg = aggregate("age", filter=Q(name__startswith="test"))
                self.assertEqual(
                    Author.objects.aggregate(age=agg)["age"], expected_result
                )