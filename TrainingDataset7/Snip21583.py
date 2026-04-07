def test_filter_with_aggregation_in_value(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.values(*self.group_by_fields)
            .annotate(
                min=Min("fk_rel__integer"),
                max=Max("fk_rel__integer"),
            )
            .filter(
                integer2=Case(
                    When(integer=2, then="min"),
                    When(integer=3, then="max"),
                ),
            )
            .order_by("pk"),
            [(3, 4, 3, 4), (2, 2, 2, 3), (3, 4, 3, 4)],
            transform=itemgetter("integer", "integer2", "min", "max"),
        )