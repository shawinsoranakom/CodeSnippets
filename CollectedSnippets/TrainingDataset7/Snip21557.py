def test_annotate_with_annotation_in_predicate(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                f_minus_2=F("integer") - 2,
            )
            .annotate(
                test=Case(
                    When(f_minus_2=-1, then=Value("negative one")),
                    When(f_minus_2=0, then=Value("zero")),
                    When(f_minus_2=1, then=Value("one")),
                    default=Value("other"),
                ),
            )
            .order_by("pk"),
            [
                (1, "negative one"),
                (2, "zero"),
                (3, "one"),
                (2, "zero"),
                (3, "one"),
                (3, "one"),
                (4, "other"),
            ],
            transform=attrgetter("integer", "test"),
        )