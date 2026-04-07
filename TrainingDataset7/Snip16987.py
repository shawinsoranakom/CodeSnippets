def test_expression_on_aggregation(self):
        qs = (
            Publisher.objects.annotate(
                price_or_median=Greatest(
                    Avg("book__rating", output_field=DecimalField()), Avg("book__price")
                )
            )
            .filter(price_or_median__gte=F("num_awards"))
            .order_by("num_awards")
        )
        self.assertQuerySetEqual(qs, [1, 3, 7, 9], lambda v: v.num_awards)

        qs2 = (
            Publisher.objects.annotate(
                rating_or_num_awards=Greatest(
                    Avg("book__rating"), F("num_awards"), output_field=FloatField()
                )
            )
            .filter(rating_or_num_awards__gt=F("num_awards"))
            .order_by("num_awards")
        )
        self.assertQuerySetEqual(qs2, [1, 3], lambda v: v.num_awards)