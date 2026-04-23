def test_aggregation_default_passed_another_aggregate(self):
        result = Book.objects.aggregate(
            value=Sum("price", filter=Q(rating__lt=3.0), default=Avg("pages") / 10.0),
        )
        self.assertAlmostEqual(result["value"], Decimal("61.72"), places=2)