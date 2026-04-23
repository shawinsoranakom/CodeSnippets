def test_annotate_with_in_clause(self):
        fk_rels = FKCaseTestModel.objects.filter(integer__in=[5])
        self.assertQuerySetEqual(
            CaseTestModel.objects.only("pk", "integer")
            .annotate(
                in_test=Sum(
                    Case(
                        When(fk_rel__in=fk_rels, then=F("fk_rel__integer")),
                        default=Value(0),
                    )
                )
            )
            .order_by("pk"),
            [(1, 0), (2, 0), (3, 0), (2, 0), (3, 0), (3, 0), (4, 5)],
            transform=attrgetter("integer", "in_test"),
        )