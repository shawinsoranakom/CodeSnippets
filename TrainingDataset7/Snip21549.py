def test_annotate_with_expression_as_value(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                f_test=Case(
                    When(integer=1, then=F("integer") + 1),
                    When(integer=2, then=F("integer") + 3),
                    default="integer",
                )
            ).order_by("pk"),
            [(1, 2), (2, 5), (3, 3), (2, 5), (3, 3), (3, 3), (4, 4)],
            transform=attrgetter("integer", "f_test"),
        )