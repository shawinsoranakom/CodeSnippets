def test_aggregation_default_unset(self):
        for Aggregate in [Avg, Max, Min, StdDev, Sum, Variance]:
            with self.subTest(Aggregate):
                result = Author.objects.filter(age__gt=100).aggregate(
                    value=Aggregate("age"),
                )
                self.assertIsNone(result["value"])