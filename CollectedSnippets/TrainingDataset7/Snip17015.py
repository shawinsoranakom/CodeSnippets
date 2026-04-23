def test_aggregation_default_zero(self):
        for Aggregate in [Avg, Max, Min, StdDev, Sum, Variance]:
            with self.subTest(Aggregate):
                result = Author.objects.filter(age__gt=100).aggregate(
                    value=Aggregate("age", default=0),
                )
                self.assertEqual(result["value"], 0)