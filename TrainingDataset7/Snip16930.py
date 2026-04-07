def test_multiple_aggregates(self):
        vals = Author.objects.aggregate(Sum("age"), Avg("age"))
        self.assertEqual(
            vals, {"age__sum": 337, "age__avg": Approximate(37.4, places=1)}
        )