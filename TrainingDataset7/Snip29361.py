def test_order_by_case_when_constant_value(self):
        qs = Article.objects.order_by(
            Case(
                When(pk__in=[], then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ).desc(),
            "pk",
        )
        self.assertSequenceEqual(qs, [self.a1, self.a2, self.a3, self.a4])