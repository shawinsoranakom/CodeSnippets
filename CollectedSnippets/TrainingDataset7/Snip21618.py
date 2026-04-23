def test_lookup_different_fields(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                test=Case(
                    When(integer=2, integer2=3, then=Value("when")),
                    default=Value("default"),
                ),
            ).order_by("pk"),
            [
                (1, 1, "default"),
                (2, 3, "when"),
                (3, 4, "default"),
                (2, 2, "default"),
                (3, 4, "default"),
                (3, 3, "default"),
                (4, 5, "default"),
            ],
            transform=attrgetter("integer", "integer2", "test"),
        )