def test_annotate_with_aggregation_in_predicate(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.values(*self.group_by_fields)
            .annotate(
                max=Max("fk_rel__integer"),
            )
            .annotate(
                test=Case(
                    When(max=3, then=Value("max = 3")),
                    When(max=4, then=Value("max = 4")),
                    default=Value(""),
                ),
            )
            .order_by("pk"),
            [
                (1, 1, ""),
                (2, 3, "max = 3"),
                (3, 4, "max = 4"),
                (2, 3, "max = 3"),
                (3, 4, "max = 4"),
                (3, 4, "max = 4"),
                (4, 5, ""),
            ],
            transform=itemgetter("integer", "max", "test"),
        )