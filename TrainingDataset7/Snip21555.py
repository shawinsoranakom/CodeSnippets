def test_annotate_with_annotation_in_value(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                f_plus_1=F("integer") + 1,
                f_plus_3=F("integer") + 3,
            )
            .annotate(
                f_test=Case(
                    When(integer=1, then="f_plus_1"),
                    When(integer=2, then="f_plus_3"),
                    default="integer",
                ),
            )
            .order_by("pk"),
            [(1, 2), (2, 5), (3, 3), (2, 5), (3, 3), (3, 3), (4, 4)],
            transform=attrgetter("integer", "f_test"),
        )