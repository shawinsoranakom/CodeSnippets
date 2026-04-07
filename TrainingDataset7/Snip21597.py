def test_update_decimal(self):
        CaseTestModel.objects.update(
            decimal=Case(
                When(integer=1, then=Decimal("1.1")),
                When(
                    integer=2, then=Value(Decimal("2.2"), output_field=DecimalField())
                ),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, Decimal("1.1")),
                (2, Decimal("2.2")),
                (3, None),
                (2, Decimal("2.2")),
                (3, None),
                (3, None),
                (4, None),
            ],
            transform=attrgetter("integer", "decimal"),
        )