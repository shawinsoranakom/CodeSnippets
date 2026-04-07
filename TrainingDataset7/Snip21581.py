def test_filter_with_annotation_in_condition(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                f_plus_1=F("integer") + 1,
            )
            .filter(
                integer=Case(
                    When(integer2=F("integer"), then=2),
                    When(integer2=F("f_plus_1"), then=3),
                ),
            )
            .order_by("pk"),
            [(3, 4), (2, 2), (3, 4)],
            transform=attrgetter("integer", "integer2"),
        )