def test_annotate_with_aggregation_in_condition(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.values(*self.group_by_fields)
            .annotate(
                min=Min("fk_rel__integer"),
                max=Max("fk_rel__integer"),
            )
            .annotate(
                test=Case(
                    When(integer2=F("min"), then=Value("min")),
                    When(integer2=F("max"), then=Value("max")),
                ),
            )
            .order_by("pk"),
            [
                (1, 1, "min"),
                (2, 3, "max"),
                (3, 4, "max"),
                (2, 2, "min"),
                (3, 4, "max"),
                (3, 3, "min"),
                (4, 5, "min"),
            ],
            transform=itemgetter("integer", "integer2", "test"),
        )