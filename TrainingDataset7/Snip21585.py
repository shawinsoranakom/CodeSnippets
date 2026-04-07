def test_filter_with_aggregation_in_predicate(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.values(*self.group_by_fields)
            .annotate(
                max=Max("fk_rel__integer"),
            )
            .filter(
                integer=Case(
                    When(max=3, then=2),
                    When(max=4, then=3),
                ),
            )
            .order_by("pk"),
            [(2, 3, 3), (3, 4, 4), (2, 2, 3), (3, 4, 4), (3, 3, 4)],
            transform=itemgetter("integer", "integer2", "max"),
        )