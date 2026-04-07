def test_cast_from_python(self):
        numbers = Author.objects.annotate(
            cast_float=Cast(decimal.Decimal(0.125), models.FloatField())
        )
        cast_float = numbers.get().cast_float
        self.assertIsInstance(cast_float, float)
        self.assertEqual(cast_float, 0.125)