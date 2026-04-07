def test_cast_to_decimal_field(self):
        FloatModel.objects.create(f1=-1.934, f2=3.467)
        float_obj = FloatModel.objects.annotate(
            cast_f1_decimal=Cast(
                "f1", models.DecimalField(max_digits=8, decimal_places=2)
            ),
            cast_f2_decimal=Cast(
                "f2", models.DecimalField(max_digits=8, decimal_places=1)
            ),
        ).get()
        self.assertEqual(float_obj.cast_f1_decimal, decimal.Decimal("-1.93"))
        expected = "3.4" if connection.features.rounds_to_even else "3.5"
        self.assertEqual(float_obj.cast_f2_decimal, decimal.Decimal(expected))
        author_obj = Author.objects.annotate(
            cast_alias_decimal=Cast(
                "alias", models.DecimalField(max_digits=8, decimal_places=2)
            ),
        ).get()
        self.assertEqual(author_obj.cast_alias_decimal, decimal.Decimal("1"))