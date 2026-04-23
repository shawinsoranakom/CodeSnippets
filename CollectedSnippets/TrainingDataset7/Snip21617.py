def test_lookup_in_condition(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                test=Case(
                    When(integer__lt=2, then=Value("less than 2")),
                    When(integer__gt=2, then=Value("greater than 2")),
                    default=Value("equal to 2"),
                ),
            ).order_by("pk"),
            [
                (1, "less than 2"),
                (2, "equal to 2"),
                (3, "greater than 2"),
                (2, "equal to 2"),
                (3, "greater than 2"),
                (3, "greater than 2"),
                (4, "greater than 2"),
            ],
            transform=attrgetter("integer", "test"),
        )