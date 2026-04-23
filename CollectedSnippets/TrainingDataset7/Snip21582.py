def test_filter_with_annotation_in_predicate(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                f_plus_1=F("integer") + 1,
            )
            .filter(
                integer2=Case(
                    When(f_plus_1=3, then=3),
                    When(f_plus_1=4, then=4),
                    default=1,
                ),
            )
            .order_by("pk"),
            [(1, 1), (2, 3), (3, 4), (3, 4)],
            transform=attrgetter("integer", "integer2"),
        )