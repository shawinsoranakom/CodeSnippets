def test_decimal_division_literal_value(self):
        """
        Division with a literal Decimal value preserves precision.
        """
        num = Number.objects.create(integer=2)
        obj = Number.objects.annotate(
            val=F("integer") / Value(Decimal("3.0"), output_field=DecimalField())
        ).get(pk=num.pk)
        self.assertAlmostEqual(obj.val, Decimal("0.6667"), places=4)