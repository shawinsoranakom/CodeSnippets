def test_aggregate(self):
        tests = [
            Q(daily_sales__sale_date__gte=self.sales_date2),
            ~Q(daily_sales__seller=self.seller1),
        ]
        for condition in tests:
            with self.subTest(condition=condition):
                qs = (
                    Book.objects.annotate(
                        recent_sales=FilteredRelation(
                            "daily_sales", condition=condition
                        ),
                        recent_sales_rates=FilteredRelation(
                            "recent_sales__currency__rates_from",
                            condition=Q(
                                recent_sales__currency__rates_from__rate_date=F(
                                    "recent_sales__sale_date"
                                ),
                                recent_sales__currency__rates_from__to_currency=(
                                    self.usd
                                ),
                            ),
                        ),
                    )
                    .annotate(
                        sales_sum=Sum(
                            F("recent_sales__sales") * F("recent_sales_rates__rate"),
                            output_field=DecimalField(),
                        ),
                    )
                    .values("title", "sales_sum")
                    .order_by(
                        F("sales_sum").desc(nulls_last=True),
                    )
                )
                self.assertSequenceEqual(
                    qs,
                    [
                        {"title": self.book2.title, "sales_sum": Decimal(150.00)},
                        {"title": self.book1.title, "sales_sum": Decimal(50.00)},
                        {"title": self.book3.title, "sales_sum": None},
                    ],
                )