def test_filter_with_aggregation_in_condition(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.values(*self.group_by_fields)
            .annotate(
                min=Min("fk_rel__integer"),
                max=Max("fk_rel__integer"),
            )
            .filter(
                integer=Case(
                    When(integer2=F("min"), then=2),
                    When(integer2=F("max"), then=3),
                ),
            )
            .order_by("pk"),
            [(3, 4, 3, 4), (2, 2, 2, 3), (3, 4, 3, 4)],
            transform=itemgetter("integer", "integer2", "min", "max"),
        )