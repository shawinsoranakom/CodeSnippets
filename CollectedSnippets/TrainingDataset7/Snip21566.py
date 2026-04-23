def test_combined_expression(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                test=Case(
                    When(integer=1, then=2),
                    When(integer=2, then=1),
                    default=3,
                )
                + 1,
            ).order_by("pk"),
            [(1, 3), (2, 2), (3, 4), (2, 2), (3, 4), (3, 4), (4, 4)],
            transform=attrgetter("integer", "test"),
        )