def test_filter_with_join_in_predicate(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(
                integer2=Case(
                    When(o2o_rel__integer=1, then=1),
                    When(o2o_rel__integer=2, then=3),
                    When(o2o_rel__integer=3, then=4),
                )
            ).order_by("pk"),
            [(1, 1), (2, 3), (3, 4), (3, 4)],
            transform=attrgetter("integer", "integer2"),
        )