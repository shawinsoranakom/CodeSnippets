def test_conditional_expression(self):
        qs = Season.objects.annotate(
            century=Case(
                When(
                    GreaterThan(F("year"), 1900) & LessThanOrEqual(F("year"), 2000),
                    then=Value("20th"),
                ),
                default=Value("other"),
            )
        ).values("year", "century")
        self.assertCountEqual(
            qs,
            [
                {"year": 1942, "century": "20th"},
                {"year": 1842, "century": "other"},
                {"year": 2042, "century": "other"},
            ],
        )