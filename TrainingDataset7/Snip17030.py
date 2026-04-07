def test_aggregation_default_using_decimal_from_database(self):
        result = Book.objects.filter(rating__lt=3.0).aggregate(
            value=Sum("price", default=Pi()),
        )
        self.assertAlmostEqual(result["value"], Decimal.from_float(math.pi), places=6)