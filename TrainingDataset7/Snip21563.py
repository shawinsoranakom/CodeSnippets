def test_annotate_values_not_in_order_by(self):
        self.assertEqual(
            list(
                CaseTestModel.objects.annotate(
                    test=Case(
                        When(integer=1, then=Value("one")),
                        When(integer=2, then=Value("two")),
                        When(integer=3, then=Value("three")),
                        default=Value("other"),
                    )
                )
                .order_by("test")
                .values_list("integer", flat=True)
            ),
            [1, 4, 3, 3, 3, 2, 2],
        )