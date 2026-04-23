def test_filter_with_annotation_in_value(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                f=F("integer"),
                f_plus_1=F("integer") + 1,
            )
            .filter(
                integer2=Case(
                    When(integer=2, then="f_plus_1"),
                    When(integer=3, then="f"),
                ),
            )
            .order_by("pk"),
            [(2, 3), (3, 3)],
            transform=attrgetter("integer", "integer2"),
        )