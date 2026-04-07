def test_aggregation_empty_cases(self):
        tests = [
            # Empty cases and default.
            (Case(output_field=IntegerField()), None),
            # Empty cases and a constant default.
            (Case(default=Value("empty")), "empty"),
            # Empty cases and column in the default.
            (Case(default=F("url")), ""),
        ]
        for case, value in tests:
            with self.subTest(case=case):
                self.assertQuerySetEqual(
                    CaseTestModel.objects.values("string")
                    .annotate(
                        case=case,
                        integer_sum=Sum("integer"),
                    )
                    .order_by("string"),
                    [
                        ("1", value, 1),
                        ("2", value, 4),
                        ("3", value, 9),
                        ("4", value, 4),
                    ],
                    transform=itemgetter("string", "case", "integer_sum"),
                )