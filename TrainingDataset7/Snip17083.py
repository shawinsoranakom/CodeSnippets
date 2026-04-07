def test_annotated_conditional_aggregate(self):
        annotated_qs = Book.objects.annotate(
            discount_price=F("price") * Decimal("0.75")
        )
        self.assertAlmostEqual(
            annotated_qs.aggregate(
                test=Avg(
                    Case(
                        When(pages__lt=400, then="discount_price"),
                        output_field=DecimalField(),
                    )
                )
            )["test"],
            Decimal("22.27"),
            places=2,
        )