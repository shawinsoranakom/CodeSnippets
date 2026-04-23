def test_update_with_expression_as_value(self):
        CaseTestModel.objects.update(
            integer=Case(
                When(integer=1, then=F("integer") + 1),
                When(integer=2, then=F("integer") + 3),
                default="integer",
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [("1", 2), ("2", 5), ("3", 3), ("2", 5), ("3", 3), ("3", 3), ("4", 4)],
            transform=attrgetter("string", "integer"),
        )