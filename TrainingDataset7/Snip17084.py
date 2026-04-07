def test_distinct_conditional_aggregate(self):
        self.assertEqual(
            Book.objects.distinct().aggregate(
                test=Avg(
                    Case(
                        When(price=Decimal("29.69"), then="pages"),
                        output_field=IntegerField(),
                    )
                )
            )["test"],
            325,
        )