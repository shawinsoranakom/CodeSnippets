def test_annotate_with_join_in_predicate(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                join_test=Case(
                    When(o2o_rel__integer=1, then=Value("one")),
                    When(o2o_rel__integer=2, then=Value("two")),
                    When(o2o_rel__integer=3, then=Value("three")),
                    default=Value("other"),
                )
            ).order_by("pk"),
            [
                (1, "one"),
                (2, "two"),
                (3, "three"),
                (2, "two"),
                (3, "three"),
                (3, "three"),
                (4, "one"),
            ],
            transform=attrgetter("integer", "join_test"),
        )