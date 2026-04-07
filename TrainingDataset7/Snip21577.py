def test_filter_with_join_in_value(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(
                integer2=Case(
                    When(integer=2, then=F("o2o_rel__integer") + 1),
                    When(integer=3, then=F("o2o_rel__integer")),
                    default="o2o_rel__integer",
                )
            ).order_by("pk"),
            [(1, 1), (2, 3), (3, 3)],
            transform=attrgetter("integer", "integer2"),
        )