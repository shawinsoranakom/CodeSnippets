def test_annotate_with_join_in_condition(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                join_test=Case(
                    When(integer2=F("o2o_rel__integer"), then=Value("equal")),
                    When(integer2=F("o2o_rel__integer") + 1, then=Value("+1")),
                    default=Value("other"),
                )
            ).order_by("pk"),
            [
                (1, "equal"),
                (2, "+1"),
                (3, "+1"),
                (2, "equal"),
                (3, "+1"),
                (3, "equal"),
                (4, "other"),
            ],
            transform=attrgetter("integer", "join_test"),
        )