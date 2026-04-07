def test_update(self):
        CaseTestModel.objects.update(
            string=Case(
                When(integer=1, then=Value("one")),
                When(integer=2, then=Value("two")),
                default=Value("other"),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, "one"),
                (2, "two"),
                (3, "other"),
                (2, "two"),
                (3, "other"),
                (3, "other"),
                (4, "other"),
            ],
            transform=attrgetter("integer", "string"),
        )