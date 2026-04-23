def test_conditional_aggregate_on_complex_condition(self):
        self.assertEqual(
            Book.objects.distinct().aggregate(
                test=Avg(
                    Case(
                        When(
                            Q(price__gte=Decimal("29")) & Q(price__lt=Decimal("30")),
                            then="pages",
                        ),
                        output_field=IntegerField(),
                    )
                )
            )["test"],
            325,
        )