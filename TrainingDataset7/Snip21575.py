def test_filter_with_expression_as_value(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(
                integer2=Case(
                    When(integer=2, then=F("integer") + 1),
                    When(integer=3, then=F("integer")),
                    default="integer",
                )
            ).order_by("pk"),
            [(1, 1), (2, 3), (3, 3)],
            transform=attrgetter("integer", "integer2"),
        )