def test_aggregation_default_using_decimal_from_python(self):
        result = Book.objects.filter(rating__lt=3.0).aggregate(
            value=Sum("price", default=Decimal("0.00")),
        )
        self.assertEqual(result["value"], Decimal("0.00"))