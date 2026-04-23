def test_annotation_with_value(self):
        values = (
            Book.objects.filter(
                name="Practical Django Projects",
            )
            .annotate(
                discount_price=F("price") * 2,
            )
            .values(
                "discount_price",
            )
            .annotate(sum_discount=Sum("discount_price"))
        )
        with self.assertNumQueries(1) as ctx:
            self.assertSequenceEqual(
                values,
                [
                    {
                        "discount_price": Decimal("59.38"),
                        "sum_discount": Decimal("59.38"),
                    }
                ],
            )
        if connection.features.allows_group_by_select_index:
            self.assertIn("GROUP BY 1", ctx[0]["sql"])