def test_filter_decimal_expression(self):
        obj = Number.objects.create(integer=0, float=1, decimal_value=Decimal("1"))
        qs = Number.objects.annotate(
            x=ExpressionWrapper(Value(1), output_field=DecimalField()),
        ).filter(Q(x=1, integer=0) & Q(x=Decimal("1")))
        self.assertSequenceEqual(qs, [obj])