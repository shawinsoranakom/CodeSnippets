def test_filter_with_join_in_condition(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(
                integer=Case(
                    When(integer2=F("o2o_rel__integer") + 1, then=2),
                    When(integer2=F("o2o_rel__integer"), then=3),
                )
            ).order_by("pk"),
            [(2, 3), (3, 3)],
            transform=attrgetter("integer", "integer2"),
        )