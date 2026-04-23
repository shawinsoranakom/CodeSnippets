def test_annotate_with_join_in_value(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                join_test=Case(
                    When(integer=1, then=F("o2o_rel__integer") + 1),
                    When(integer=2, then=F("o2o_rel__integer") + 3),
                    default="o2o_rel__integer",
                )
            ).order_by("pk"),
            [(1, 2), (2, 5), (3, 3), (2, 5), (3, 3), (3, 3), (4, 1)],
            transform=attrgetter("integer", "join_test"),
        )