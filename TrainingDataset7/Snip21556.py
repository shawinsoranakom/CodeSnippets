def test_annotate_with_annotation_in_condition(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                f_plus_1=F("integer") + 1,
            )
            .annotate(
                f_test=Case(
                    When(integer2=F("integer"), then=Value("equal")),
                    When(integer2=F("f_plus_1"), then=Value("+1")),
                ),
            )
            .order_by("pk"),
            [
                (1, "equal"),
                (2, "+1"),
                (3, "+1"),
                (2, "equal"),
                (3, "+1"),
                (3, "equal"),
                (4, "+1"),
            ],
            transform=attrgetter("integer", "f_test"),
        )