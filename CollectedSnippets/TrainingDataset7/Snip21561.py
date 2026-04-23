def test_annotate_exclude(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                test=Case(
                    When(integer=1, then=Value("one")),
                    When(integer=2, then=Value("two")),
                    default=Value("other"),
                )
            )
            .exclude(test="other")
            .order_by("pk"),
            [(1, "one"), (2, "two"), (2, "two")],
            transform=attrgetter("integer", "test"),
        )